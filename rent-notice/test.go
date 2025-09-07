package main

import (
	"context"
	"encoding/json"
	"os"
	"testing"
	"time"

	"github.com/disgoorg/disgo/bot"
)

func TestNoticeServer_readSendRent(t *testing.T) {
	// Mock bot.Client (replace with a real mock if needed for more complex tests)
	mockClient := &bot.ClientImpl{}

	// Test file path
	testFilePath := "test.json"

	// Initial renter data
	initialRenter := Renter{
		UserId:       841645602014101554,
		ChannelId:    1381597629330227240,
		Email:        "thanhtra2004@gmail.com",
		RentAmount:   260,
		TimeLastPaid: 1756121352,
	}

	// Create test file
	initialRenterBytes, _ := json.Marshal(initialRenter)
	err := os.WriteFile(testFilePath, initialRenterBytes, 0644)
	if err != nil {
		t.Fatalf("failed to create test file: %v", err)
	}
	defer os.Remove(testFilePath) // Clean up after the test

	// Instantiate NoticeServer
	noticeServer := &NoticeServer{Client: mockClient}

	// Call readSendRent
	err = noticeServer.readSendRent(context.Background(), testFilePath)
	if err != nil {
		t.Fatalf("readSendRent failed: %v", err)
	}

	// Read the modified test file
	updatedRenterBytes, err := os.ReadFile(testFilePath)
	if err != nil {
		t.Fatalf("failed to read updated test file: %v", err)
	}

	var updatedRenter Renter
	err = json.Unmarshal(updatedRenterBytes, &updatedRenter)
	if err != nil {
		t.Fatalf("failed to unmarshal updated renter data: %v", err)
	}

	// Assert that unix_time_last_paid has changed
	if updatedRenter.TimeLastPaid == initialRenter.TimeLastPaid {
		t.Errorf("unix_time_last_paid did not change. old=%d, new=%d", initialRenter.TimeLastPaid, updatedRenter.TimeLastPaid)
	}

	// Assert that unix_time_last_paid is approximately the current time
	currentTime := time.Now().Unix()
	const tolerance = 5 // seconds
	if updatedRenter.TimeLastPaid < currentTime-tolerance || updatedRenter.TimeLastPaid > currentTime+tolerance {
		t.Errorf(
			"unix_time_last_paid is not approximately the current time. expected ~%d, got %d",
			currentTime,
			updatedRenter.TimeLastPaid,
		)
	}
}
