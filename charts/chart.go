package main

import (
	"database/sql"
	"fmt"
	"log/slog"
	"net/http"
	"os"
	"strings"

	"github.com/go-echarts/go-echarts/v2/charts"
	"github.com/go-echarts/go-echarts/v2/opts"

	_ "github.com/mattn/go-sqlite3"
)

type Config struct {
	DBUrl    string
	Port     string
	SaveAcc  string
	SpendAcc string
}

type Transaction struct {
	AccountID     string
	TransactionID string
	AccountName   string
	Amount        int64
	Time          int64
	Vendor        string
	Category      string
	Location      string
	Description   string
}

const SECONDS_IN_WEEK = 60 * 60 * 24 * 7

var (
	db   *sql.DB
	conf Config
)

func init() {
	port, ok := os.LookupEnv("ECHART_PORT")
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

	save, ok := os.LookupEnv("SHARED_SAVE_ACCOUNT_ID")
	if !ok {
		panic("could not read save acc id from env")
	}
	conf.SaveAcc = save

	spend, ok := os.LookupEnv("SHARED_SPEND_ACCOUNT_ID")
	if !ok {
		panic("could not read spend acc id from env")
	}
	conf.SpendAcc = spend

	var err error
	db, err = sql.Open("sqlite3", url)
	if err != nil {
		slog.Error("error while opening db", slog.Any("err", err))
		return
	}
}

func getTransFromDB() ([]*Transaction, error) {
	sqlStatement := `SELECT * FROM transactions ORDER BY time;`

	var transactions []*Transaction
	rows, err := db.Query(sqlStatement)
	if err != nil {
		return nil, err
	}
	for rows.Next() {
		t := &Transaction{}
		err := rows.Scan(
			&t.AccountID,
			&t.TransactionID,
			&t.AccountName,
			&t.Amount,
			&t.Time,
			&t.Vendor,
			&t.Category,
			&t.Location,
			&t.Description,
		)
		if err != nil {
			return nil, err
		}
		transactions = append(transactions, t)
	}

	return transactions, nil
}

// TODO Aggregate items by week
func generateLineItems(accountID string, transactions []*Transaction) ([]opts.LineData, []int64) {
	items := make([]opts.LineData, 0)
	times := make([]int64, 0)
	first := transactions[0].Time
	for _, t := range transactions {
		if t.AccountID != accountID {
			continue
		}
		items = append(items, opts.LineData{Value: t.Amount / 100})
		times = append(times, (t.Time-first)/SECONDS_IN_WEEK)
	}
	return items, times
}

func generateCumLineItems(accountID string, transactions []*Transaction) ([]opts.LineData, []int64) {
	total := int64(0)
	items := make([]opts.LineData, 0)
	times := make([]int64, 0)
	first := transactions[0].Time
	for _, t := range transactions {
		if t.AccountID != accountID {
			continue
		}
		total += t.Amount
		items = append(items, opts.LineData{Value: t.Amount / 100})
		times = append(times, (t.Time-first)/SECONDS_IN_WEEK)
	}
	return items, times
}

func httpserver(w http.ResponseWriter, _ *http.Request) {
	transactions, err := getTransFromDB()
	if err != nil {
		w.WriteHeader(500)
		return
	}
	lineSpend := charts.NewLine()
	lineSave := charts.NewLine()

	// line.SetGlobalOptions(
	// 	charts.WithInitializationOpts(opts.Initialization{Theme: types.ThemeWesteros}),
	// 	charts.WithTitleOpts(opts.Title{
	// 		Title:    "Line example in Westeros theme",
	// 		Subtitle: "Line chart rendered by the http server this time",
	// 	}))

	items, times := generateLineItems(conf.SpendAcc, transactions)
	lineSpend.SetXAxis(times).
		AddSeries("Category A", items)
		// SetSeriesOptions(charts.WithLineChartOpts(opts.LineChart{Smooth: opts.Bool(true)}))
	lineSpend.Render(w)

	items, times = generateCumLineItems(conf.SaveAcc, transactions)
	lineSave.SetXAxis(times).
		AddSeries("Category A", items)
	lineSave.Render(w)
}

func main() {
	http.HandleFunc("/", httpserver)
	fmt.Printf("listening on port %s", conf.Port)
	http.ListenAndServe(fmt.Sprintf(":%s", conf.Port), nil)
	defer db.Close()
}
