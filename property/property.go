package main

import (
	"context"
	"fmt"
	"os"

	"github.com/jackc/pgx/v5"
)

type PropertySale struct {
	AptNum       string `json:"apt_num"`
	StreetNum    string `json:"street_num"`
	Street       string `json:"json_street"`
	Postcode     int    `json:"postcode"`
	ListingPrice int    `json:"listing_price"`
	SquareMtr    int    `json:"square_mtr"`
	SellTime     int    `json:"sell_time"` // unix timestamp
	Bedrooms     int    `json:"bedrooms"`
	Bathrooms    int    `json:"bathrooms"`
	CarSpaces    int    `json:"car_spaces"`
	WaterRates   int    `json:"water_rates"`
	CouncilRates int    `json:"council_rates"`
	Strata       int    `json:"strata"`
}

func linearRegression(sales []PropertySale) (m, c float64) {
	var sumX, sumY, sumXY, sumX2 float64
	n := float64(len(sales))

	if n == 0 {
		return 0, 0
	}

	for _, s := range sales {
		x := float64(s.SellTime)
		y := float64(s.ListingPrice)
		sumX += x
		sumY += y
		sumXY += x * y
		sumX2 += x * x
	}

	// m = (n*Σ(xy) - Σx*Σy) / (n*Σ(x^2) - (Σx)^2)
	denominator := (n*sumX2 - sumX*sumX)
	if denominator == 0 {
		return 0, 0 // Avoid division by zero, should not happen with varied SellTime
	}
	m = (n*sumXY - sumX*sumY) / denominator
	// c = (Σy - m*Σx) / n
	c = (sumY - m*sumX) / n
	return m, c
}

func main() {
	ctx := context.Background()
	connStr := os.Getenv("NEON_DB_PROPERTY_URL")
	conn, err := pgx.Connect(ctx, connStr)
	if err != nil {
		panic(err)
	}
	rows, err := conn.Query(
		ctx,
		"SELECT apt_num, street_num, street, postcode, listing_price, square_mtr, sell_time, bedrooms, bathrooms, car_spaces, water_rates, council_rates, strata FROM property_sale ORDER BY listing_price",
	)
	if err != nil {
		panic(err)
	}
	defer rows.Close()

	var propertySales []PropertySale
	propertySales, err = pgx.CollectRows(rows, pgx.RowToStructByPos[PropertySale])
	if err != nil {
		panic(err)
	}

	m, c := linearRegression(propertySales)
	fmt.Printf("Linear Regression Model: Price = %.2f * SellTime + %.2f\n", m, c)

	for _, sale := range propertySales {
		fmt.Printf(
			"Apt: %s, street_num: %s, Street: %s, Price: %d\n",
			sale.AptNum,
			sale.StreetNum,
			sale.Street,
			sale.ListingPrice,
		)
	}
}

