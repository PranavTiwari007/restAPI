# **Aircraft Tracking API — Project Documentation** 

## **1. Introduction** 

The Aircraft Tracking API is a Python-based REST API project that retrieves aircraft state information from the OpenSky Network API, stores it in a local SQLite database, and allows users to retrieve the saved information through our own API endpoints. 

## **2. Why We Chose This API** 

We chose the OpenSky Network API because it provides real-world aircraft data, including aircraft location, altitude, speed, and direction. It helps us understand how external REST APIs work and how their data can be integrated into our own applications. 

## **3. Proposed Idea** 

Our idea is to build an application that imports aircraft data for a selected geographical area, stores the retrieved information, and provides endpoints to access the saved data. 

The application acts as an intermediary between OpenSky and the client, making the data available through our own API. 

## **4. Technologies Used** 

- **Python and FastAPI:** To develop our REST API. 

- **OpenSky Network API:** To retrieve aircraft information. 

- **HTTPX:** To communicate with the external API. 

- **SQLite:** To store aircraft records and import snapshots. 

- **Pydantic:** To validate incoming data and structure responses. 

- **Swagger UI:** To test the endpoints. 

## **5. How the Project Works** 

1. The client submits a geographical area through a POST request. 

2. The application validates the coordinates and authenticates with OpenSky. 

3. Aircraft data is retrieved from OpenSky. 

4. The returned data is converted into a structured format. 

5. The data and its import details are saved in SQLite. 

6. The client can retrieve the saved aircraft data through GET requests. 

## **6. API Endpoints** 

|**Method**|**Endpoint**|**Purpose**|
|---|---|---|
|GET|/health|Checks whether the application is running.|
|POST|/api/v1/state-imports|Retrieves aircraft data from OpenSky and saves<br>it to the database.|
|GET|/api/v1/aircraft-states|Retrieves the latest saved snapshot and its<br>aircraft records.|
|GET|/api/v1/aircraft-states<br>/{state_id}|Retrieves one aircraft-state record using its<br>database ID.|



### **Why Do We Use These Requests?** 

- **GET /health :** To verify that the API is working. 

- **POST /api/v1/state-imports :** To fetch and store aircraft data for a specified geographical area. 


- **GET /api/v1/aircraft-states :** To retrieve all aircraft records from the latest saved 

- **GET /api/v1/aircraft-states/{state_id} :** To retrieve a particular aircraft record instead of the entire collection. 


## **7. Purpose and Applications** 

This project demonstrates external API integration, data validation, database storage, and REST endpoint development. It can serve as a foundation for future applications such as aircraft monitoring dashboards, map-based visualizations, and historical aircraft-data analysis. 

## **8. Conclusion** 

The project demonstrates how an external REST API can be integrated with a Python backend to retrieve, process, store, and serve real-world data. It provides practical experience with HTTP methods, authentication, JSON responses, database operations, and API testing. 

