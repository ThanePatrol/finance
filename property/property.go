package property

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
