package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"math"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/disgoorg/disgo"
	"github.com/disgoorg/disgo/bot"
	"github.com/disgoorg/disgo/discord"
	"github.com/disgoorg/disgo/gateway"
	"github.com/disgoorg/snowflake/v2"

	_ "github.com/mattn/go-sqlite3"
)

const (
	DAYS_IN_WEEK   = 7
	SECONDS_IN_DAY = float64(60 * 60 * 24)
)

type Config struct {
	Account string
	Bsb     string
	UserId  string
	Port    string
	DBUrl   string
}

var (
	conf Config
	db   *sql.DB
)

func init() {
	account, ok := os.LookupEnv("ACCOUNT")
	if !ok {
		panic("could not read account from env")
	}
	conf.Account = account
	bsb, ok := os.LookupEnv("BSB")
	if !ok {
		panic("could not read bsb from env")
	}
	conf.Bsb = bsb
	userId, ok := os.LookupEnv("DADDY_THANE_USER_ID")
	if !ok {
		panic("could not read user id from env")
	}
	conf.UserId = userId
	port, ok := os.LookupEnv("RENT_DISCORD_BOT_PORT")
	if !ok {
		slog.Error("could not read port, defaulting to 0")
		conf.Port = "0"
	} else {
		slog.Info("listening on port", slog.String("port", port))
		conf.Port = port
	}

	url, ok := os.LookupEnv("SQLITE_URL")
	if !ok {
		panic("could not read db url from env")
	}
	url = strings.ReplaceAll(url, `"`, "")
	conf.DBUrl = url
}

type Renter struct {
	UserId       uint64 `json:"user_id"`
	ChannelId    uint64 `json:"channel_id"`
	Email        string `json:"email"`
	RentAmount   int64  `json:"weekly_rent_amt"`
	TimeLastPaid int64  `json:"unix_time_last_paid"`
}

type User struct {
	Name         string `db:"name"`
	Amount       int64  `db:"amount"`
	DiscordID    int64  `db:"discord_id"`
	ChannelID    int64  `db:"channel_id"`
	TimeLastPaid int64  `db:"time"`
}

func (r *Renter) calculateRent(curTime int64) int64 {
	rentInDays := float64(r.RentAmount) / float64(DAYS_IN_WEEK)
	secondsSinceLastPay := curTime - r.TimeLastPaid
	daysSinceLastPay := float64(secondsSinceLastPay) / SECONDS_IN_DAY
	amountToPay := rentInDays * daysSinceLastPay
	return int64(amountToPay)
}

func postRent(renter *Renter, amount int64, client bot.Client) error {
	message := `
		# Rent Notice <@_USER>

        Amount owing: _OWING

        BSB: _BSB
        Account: _ACC

        Please contact <@_DADDY> within 24 hours if there are any issues! 😋

	`
	message = strings.Replace(message, "_USER", fmt.Sprintf("%d", renter.UserId), 1)
	message = strings.Replace(message, "_OWING", fmt.Sprintf("%d", amount), 1)
	message = strings.Replace(message, "_BSB", conf.Bsb, 1)
	message = strings.Replace(message, "_ACC", conf.Account, 1)
	message = strings.Replace(message, "_DADDY", conf.UserId, 1)

	var err error
	for range 3 {
		_, err = client.Rest().
			CreateMessage(snowflake.ID(renter.ChannelId), discord.NewMessageCreateBuilder().SetContent(message).Build())
		if err == nil {
			break
		}
		time.Sleep(time.Second)
	}

	if err != nil {
		slog.Error("error sending message", slog.Any("err", err))
	}
	return err
}

type NoticeServer struct {
	Client bot.Client
}

type RemindServer struct {
	Client bot.Client
}

func unixToStr(t int64) string {
	ti := time.Unix(t, 0)
	f := ti.Format("2006-01-02 15:04:05")
	return f
}

func saveRentToDB(ctx context.Context, uid, amt, curTime int64) error {
	// negative amount as they owe money
	amtInCents := -1 * (amt * 100)
	_, err := db.ExecContext(ctx, `INSERT INTO rent_payments VALUES (
		?, ?, ?, ?
	);`, uid, amtInCents, curTime, "")
	if err != nil {
		return err
	}
	return nil
}

func getRentersFromDB(ctx context.Context) ([]*User, error) {
	sqlStatement := `SELECT t.name, SUM(r.amount), t.discord_id, t.channel_id, r.time FROM rent_payments as r
LEFT JOIN renter as t
ON r.discord_id = t.discord_id
GROUP BY r.discord_id;
`

	var renters []*User
	rows, err := db.QueryContext(ctx, sqlStatement)
	if err != nil {
		return nil, err
	}
	for rows.Next() {
		us := &User{}
		_ = rows.Scan(&us.Name, &us.Amount, &us.DiscordID, &us.ChannelID, &us.TimeLastPaid)

		renters = append(renters, us)
	}

	return renters, nil
}

func getRenterPayments(ctx context.Context, uid uint64) (*User, error) {
	users, err := getRentersFromDB(ctx)
	if err != nil {
		return nil, err
	}
	for _, user := range users {
		if user.DiscordID == int64(uid) {
			return user, nil
		}
	}
	return nil, errors.New("could not find user")
}

func (s *NoticeServer) readSendRent(ctx context.Context, fp string) error {
	var renter Renter
	f, err := os.ReadFile(fp)
	if err != nil {
		return err
	}
	err = json.Unmarshal(f, &renter)
	if err != nil {
		return err
	}
	slog.InfoContext(
		ctx,
		"read from file renter ",
		slog.String("renter", renter.Email),
	)
	curTime := time.Now().Unix()
	amountToPay := renter.calculateRent(curTime)

	err = saveRentToDB(ctx, int64(renter.UserId), amountToPay, curTime)
	if err != nil {
		return err
	}

	user, err := getRenterPayments(ctx, renter.UserId)
	if err != nil {
		return err
	}

	amountPreviousOwe := -1 * user.Amount / 100

	if amountPreviousOwe > 10 {
		// user has not paid within a margin of $10
		err = postRent(&renter, amountToPay+amountPreviousOwe, s.Client)
		if err != nil {
			return err
		}
	}

	oldTime := renter.TimeLastPaid
	renter.TimeLastPaid = curTime
	renterBytes, err := json.Marshal(renter)
	if err != nil {
		return err
	}

	slog.InfoContext(
		ctx,
		"checked rent balance for ",
		slog.String("renter", renter.Email),
		slog.Int64("amount", amountToPay),
		slog.String("time last paid", unixToStr(oldTime)),
		slog.String("time paid", unixToStr(renter.TimeLastPaid)),
	)
	err = os.WriteFile(fp, renterBytes, os.ModePerm)
	if err != nil {
		return err
	}
	return nil
}

func (s *NoticeServer) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	defer r.Body.Close()
	bytedata, err := io.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "could not read file path", http.StatusBadRequest)
		return
	}
	err = s.readSendRent(r.Context(), string(bytedata))
	if err != nil {
		slog.ErrorContext(r.Context(), "could not process rent notification", slog.String("err", err.Error()))
		http.Error(w, "could not send rent", http.StatusInternalServerError)
		return
	}
	fmt.Fprintf(w, "sent rent to renter=%s", string(bytedata))
}

func (s *RemindServer) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	renters, _ := getRentersFromDB(r.Context())

	now := time.Now().Unix()
	message := `
		# Rent Reminder Notice <@_USER>

		This is an automated rent reminder. You still owe: _OWING

        Please contact <@_DADDY> within 24 hours if there are any issues! 😋

	`

	for _, renter := range renters {
		rentInDollar := int64(
			math.Abs(float64(renter.Amount / 100)),
		) // is negative in DB because they owe and DB stores in cents

		if renter.TimeLastPaid+int64(24*time.Hour) <= now || rentInDollar < 10 {
			continue
		}
		m := strings.Replace(message, "_USER", fmt.Sprintf("%d", renter.DiscordID), 1)
		m = strings.Replace(m, "_OWING", fmt.Sprintf("%d", rentInDollar), 1)
		m = strings.Replace(m, "_DADDY", conf.UserId, 1)
		var err error
		for range 3 {
			_, err = s.Client.Rest().
				CreateMessage(snowflake.ID(renter.ChannelID), discord.NewMessageCreateBuilder().SetContent(m).Build())
			if err == nil {
				break
			}
			time.Sleep(time.Second)
		}
	}
}

func setupHTTPServer(client bot.Client) {
	http.Handle("/", &NoticeServer{
		Client: client,
	})
	http.Handle("/remind", &RemindServer{
		Client: client,
	})
	http.ListenAndServe(fmt.Sprintf(":%s", conf.Port), nil)
}

func main() {
	slog.Info("starting example...")
	slog.Info("disgo version", slog.String("version", disgo.Version))

	client, err := disgo.New(os.Getenv("BOT_TOKEN"),
		bot.WithGatewayConfigOpts(
			gateway.WithIntents(
				gateway.IntentsAll,
				gateway.IntentGuildMessages,
				gateway.IntentMessageContent,
			),
		),
	)
	if err != nil {
		slog.Error("error while building disgo", slog.Any("err", err))
		return
	}
	defer client.Close(context.TODO())

	slog.Info("about to open db", slog.String("url", conf.DBUrl))
	db, err = sql.Open("sqlite3", conf.DBUrl)
	if err != nil {
		slog.Error("error while opening db", slog.Any("err", err))
		return
	}
	defer db.Close()

	if err = client.OpenGateway(context.TODO()); err != nil {
		slog.Error("errors while connecting to gateway", slog.Any("err", err))
		return
	}

	go func() {
		setupHTTPServer(client)
	}()

	slog.Info("example is now running. Press CTRL-C to exit.")
	s := make(chan os.Signal, 1)
	signal.Notify(s, syscall.SIGINT, syscall.SIGTERM, os.Interrupt)
	<-s
}
