# URL-Shortener

## Overview

The following project is a poc that allows anyone to take a long url, and shorten the url similar to [bit.ly](https://bitly.com/). This project follows a design and architecture aiming to minimize problems as the service scales to Millions of users. 
## Exact problem statement provided

The challenge is to build a HTTP-based RESTful API for managing Short URLs and redirecting clients similar to bit.ly or goo.gl. Be thoughtful that the system must eventually support millions of short urls. Please include a README with documentation on how to build, and run and test the system. Clearly state all assumptions and design decisions in the README. 

A Short Url: 

1. Has one long url 
2. Permanent; Once created 
3. Is Unique; If a long url is added twice it should result in two different short urls. 
4. Not easily discoverable; incrementing an already existing short url should have a low probability of finding a working short url. 

Your solution must support: 

1. Generating a short url from a long url 
2. Redirecting a short url to a long url within 10 ms. 
3. Listing the number of times a short url has been accessed in the last 24 hours, past week and all time. 
4. Persistence (data must survive computer restarts) 

Shortcuts 

1. No authentication is required 
2. No html, web UI is required 
3. Transport/Serialization format is your choice, but the solution should be testable via curl

## Assumptions

## How to test

**Prerequisites**
Please ensure you have Docker Desktop on your machine and can access docker commands from the cli

**Setup and testing**
To setup the service, please do the following:

Go into the ```backend``` folder of the project and run ```docker-compose up --build```.

The flask api will now be accessible at port 8080 of your local machine or http://127.0.0.1:8080 

The api allows three calls:

  1. Setting a short url for a long url

     ```curl --location 'http://127.0.0.1:8080/shorten' \
--header 'Content-Type: application/json' \
--data '  {
    "long_url": "https://dev.bitly.com",
    "title": "Bitly API Documentation",
    "tags": [
      "bitly",
      "api"
    ]
  }'```

  3. Getting a long url from a short url
  4. Getting the analytics of a short url (how many times it was accessed in the last 24 hours, week, and all time)


**Teardown**





##Technical decisions
