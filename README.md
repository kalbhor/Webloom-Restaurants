# Run the project
```
pip install -r requirements.txt
python api.py
```
#### Simultaneously 
```
mongod
```

# API methods

## Restaurant 
Accepts the following as paramaters in url to filter during GET request: id, name

### GET /api/restaurants
```
{
    "data": [
        {
            "_id": {
                "$oid": "5ed53309bba829fc7da7ade8"
            },
            "capacity": 20,
            "name": "Pai Tiffins",
            "tables": [
                {
                    "$oid": "5ed53321bba829fc7da7ade9"
                },
                {
                    "$oid": "5ed5333dbba829fc7da7adea"
                }
            ]
        },
        {
            "_id": {
                "$oid": "5ed5370fbba8290ce3ec96aa"
            },
            "capacity": 20,
            "name": "Chinese Wok",
            "tables": []
        }
    ],
    "status": "ok"
}
```
### GET /api/restaurants?name=Chinese Wok
```
{
    "data": [
        {
            "_id": {
                "$oid": "5ed5370fbba8290ce3ec96aa"
            },
            "capacity": 20,
            "name": "Chinese Wok",
            "tables": []
        }
    ],
    "status": "ok"
}
```
### POST /api/restaurants
Checks for name (if existing) and adds an empty list of table ids by default

#### Request body (JSON) 
```
{
	"capacity": 20,
	"name": "Chinese Wok"
}
```
#### Response
```
{
    "response": "Restaurant added with id 5ed5370fbba8290ce3ec96aa"
}
```

---

## Table 
Accepts the following (or combination of) as paramaters in url to filter during GET request: id, restaurant_id, flexible, booking_ids

### GET /api/tables

```
{
    "data": [ 
        {
            "_id": {
                "$oid": "5ed53348bba829fc7da7adeb"
            },
            "bookings": [],
            "flexible": false,
            "restaurant_id": "5ed53309bba829fc7da7ade8",
            "size": 4
        },
        {
            "_id": {
                "$oid": "5ed5349abba82902522d5a19"
            },
            "bookings": [
                {
                    "$oid": "5ed53546bba82906bfc7c4bf"
                }
            ],
            "flexible": true,
            "restaurant_id": "5ed53309bba829fc7da7ade8",
            "size": 1
        },
        {
            "_id": {
                "$oid": "5ed53954bba8290ce3ec96ab"
            },
            "bookings": [],
            "flexible": true,
            "restaurant_id": "5ed5370fbba8290ce3ec96aa",
            "size": 4
        }
    ],
    "status": "ok"
}
```

### GET /api/tables?restaurant_id=5ed5370fbba8290ce3ec96aa

```
{
    "data": [
        {
            "_id": {
                "$oid": "5ed53954bba8290ce3ec96ab"
            },
            "bookings": [],
            "flexible": true,
            "restaurant_id": "5ed5370fbba8290ce3ec96aa",
            "size": 4
        }
    ],
    "status": "ok"
}
```

---

## Bookings
Accepts the following as paramaters in url to filter during GET request: id, restaurant_id, time, date

### GET /api/bookings
```
{
    "data": [
        {
            "_id": {
                "$oid": "5ed5343dbba82902522d5a18"
            },
            "date": {
                "$date": 1578268800000
            },
            "name": "Lakshay Kalbhor",
            "restaurant_id": "5ed5226bbba829b3a48675cd",
            "size": 2,
            "table_ids": [
                "5ed53361bba829fc7da7aded"
            ],
            "time_end": {
                "$date": 1591045200000
            },
            "time_start": {
                "$date": 1591038000000
            }
        },
        {
            "_id": {
                "$oid": "5ed53546bba82906bfc7c4bf"
            },
            "date": {
                "$date": 1578268800000
            },
            "name": "Arnav Kalbhor",
            "restaurant_id": "5ed5226bbba829b3a48675cd",
            "size": 3,
            "table_ids": [
                "5ed53321bba829fc7da7ade9",
                "5ed5333dbba829fc7da7adea",
                "5ed5349abba82902522d5a19"
            ],
            "time_end": {
                "$date": 1591045200000
            },
            "time_start": {
                "$date": 1591038000000
            }
        }
    ],
    "status": "ok"
}
```

## POST /api/bookings
#### Request Body (In JSON)
```
{
	"name": "Rahul",
	"restaurant_id": "5ed5226bbba829b3a48675cd",
	"size" : 2,
	"date" : "1/06/2020",
	"time" : "7:00pm"
}
```
#### Response
```
{
    "response": "Booking added with id 5ed53546bba82906bfc7c4bf"
}
```

If booking slot isn't available it shall return an error ("No tables found")
