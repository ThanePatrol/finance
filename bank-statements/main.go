package main

import (
	"encoding/csv"
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"
)

type Transaction interface {
	Date() int64
	Description() string
	Amount() float64
	Balance() float64
}

type Hsbc struct {
	date        int64   `csv:"Date"`
	description string  `csv:"Description"`
	amount      float64 `csv:"Amount"`
	balance     float64 `csv:"Balance"`
}

func (h Hsbc) Date() int64 {
	return h.date
}

func (h Hsbc) Description() string {
	return h.description
}

func (h Hsbc) Amount() float64 {
	return h.amount
}

func (h Hsbc) Balance() float64 {
	return h.balance
}

func HsbcFromCsv(f [][]string) ([]Hsbc, error) {
	var hsbcs []Hsbc
	for i, line := range f {
		// Skip header row
		if i == 0 {
			continue
		}
		if len(line) != 4 {
			return nil, fmt.Errorf("line does not have 4 entries: %d", len(line))
		}
		var trimmed []string
		for _, entry := range line {
			trimmed = append(trimmed, strings.TrimSpace(entry))
		}

		// Ignore transfers
		if strings.HasPrefix(trimmed[1], "TRANSFER") {
			continue
		}

		hsbc := Hsbc{}

		date, err := time.Parse("02 Jan 2006", trimmed[0])
		if err != nil {
			return nil, fmt.Errorf("could not parse time on line %d: %w", i, err)
		}
		hsbc.date = date.Unix()

		hsbc.description = trimmed[1]

		amount, err := strconv.ParseFloat(trimmed[2], 64)
		if err != nil {
			return nil, fmt.Errorf("could not parse amount on line %d: %w", i, err)
		}
		hsbc.amount = amount

		balance, _ := strconv.ParseFloat(trimmed[3], 64)
		// if err != nil {
		//
		// 	return nil, fmt.Errorf("could not parse balance on line %d: %w", i, err)
		// }
		hsbc.balance = balance

		hsbcs = append(hsbcs, hsbc)
	}

	return hsbcs, nil
}

// TODO:
// 1 - Parameterize the reading of csvs
// 2 - Automatically download csvs from hsbc
// 3 - Download statements from ubank
// 4 - Download mac bank statements
// 5 - Save all statement data to sqlite
// 6 - Run periodically via cron/ w/e
// 7 - Visualize incomings and outgoings with go echarts 😋
// 8 - Check incoming via rent bot, check if they have actually paid, if not ping the rent bot to ping them again

func main() {
	f, err := os.Open("../../../Downloads/TransHist.csv")
	if err != nil {
		panic(fmt.Sprintf("could not read file err: %q", err.Error()))
	}
	defer f.Close()

	csvFile := csv.NewReader(f)
	trans, err := csvFile.ReadAll()
	if err != nil {
		panic(fmt.Sprintf("could not parse csv err: %q", err.Error()))
	}

	hsbcs, err := HsbcFromCsv(trans)
	if err != nil {
		panic(fmt.Sprintf("could not convert csv to hsbc: %q", err.Error()))
	}
	for _, h := range hsbcs {
		fmt.Printf("%+v\n", h.amount)
	}

	sumAmt := 0.0
	for _, hsbc := range hsbcs {
		sumAmt += hsbc.amount
	}
	fmt.Printf("%f\n", sumAmt)
}
