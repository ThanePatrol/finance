package main

import (
	"testing"

	"github.com/go-echarts/go-echarts/v2/opts"
	"github.com/google/go-cmp/cmp"
)

func TestGenerateLineItems(t *testing.T) {
	const firstTime int64 = 1672531200 // Jan 1, 2023, 00:00:00 UTC

	const secondsInWeek int64 = 60 * 60 * 24 * 7

	tests := []struct {
		name         string
		accountID    string
		transactions []*Transaction
		wantItems    []opts.LineData
		wantTimes    []int64
	}{
		{
			name:      "Filter and Convert - Basic Case",
			accountID: "SpendAccID",
			transactions: []*Transaction{
				{AccountID: "SpendAccID", Amount: 500, Time: firstTime},
				// Different account - should be skipped
				{AccountID: "SaveAccID", Amount: 2000},
				{AccountID: "SpendAccID", Amount: 1000, Time: firstTime},
				{AccountID: "SpendAccID", Amount: 1250, Time: firstTime},
			},
			wantItems: []opts.LineData{
				{Value: int64(5)},
				{Value: int64(10)},
				{Value: int64(12)},
			},
			wantTimes: []int64{0, 0, 0},
		},
		{
			name:      "Empty Transactions",
			accountID: "AnyID",
			transactions: []*Transaction{
				{AccountID: "OtherID", Amount: 1000},
			},
			wantItems: []opts.LineData{},
		},
		{
			name:      "All Transactions Skipped",
			accountID: "NonExistentID",
			transactions: []*Transaction{
				{AccountID: "A", Amount: 100},
				{AccountID: "B", Amount: 200},
			},
			wantItems: nil,
		},
		{
			name:      "Times are handled",
			accountID: "foo",
			transactions: []*Transaction{
				{AccountID: "foo", Amount: 100, Time: firstTime},
			},
			wantItems: []opts.LineData{
				{Value: int64(1)},
			},
			wantTimes: []int64{0},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			gotItems, gotTimes := generateLineItems(tt.accountID, tt.transactions)
			if len(gotItems) != len(tt.wantItems) {
				t.Errorf("generateLineItems() gotItems = %d, want = %d", len(gotItems), len(tt.wantItems))
			}

			for i, item := range gotItems {
				if item.Value.(int64) != tt.wantItems[i].Value.(int64) {
					t.Errorf("generateLineItems() got = %d, want = %d", item.Value, tt.wantItems[i].Value)
				}
			}

			if diff := cmp.Diff(gotTimes, tt.wantTimes); diff != "" {
				t.Errorf("generateLineItems() (-got +want) = %s", diff)
			}
		})
	}
}
