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


## How to test

**Prerequisites**
Please ensure you have Docker Desktop on your machine and can access docker commands from the cli

**Setup and testing**
To setup the service, please do the following:

Go into the ```backend``` folder of the project and run ```docker-compose up --build```.

The flask api will now be accessible at port 8080 of your local machine or http://127.0.0.1:8080 

The api allows three calls:

***1. Setting a short url for a long url. The following curl returns a short url.***

  ```bash
curl --location 'http://127.0.0.1:8080/shorten' \
--header 'Content-Type: application/json' \
--data '  {
    "long_url": "<YOUR-LONG-URL>",
    "back_half": "<YOUR-BACK-HALF>"
  }'

```
In the data section:

```long_url```: The long url you want to shorten. Put your long url in <YOUR-LONG-URL>
```back_half(optional)```: This is a custom short key that the user can provide. If the key has not already been used, the end of the url after the domain will be this key. If this field is empty or not provided, then a unique key will automatically be created for the user. Put the short key in <YOUR-BACK-HALF>  

Returns: A short url. 

***2. Getting a long url from a short url***

```bash
curl --location 'http://127.0.0.1:8080/<YOUR-CUSTOM-KEY>'
```
Replace <YOUR-CUSTOM-KEY> with the short key you want to find. 

Returns: the webpage that the long url for the short key links to. 
     
***3. Getting the analytics of a short url (how many times it was accessed in the last 24 hours, week, and all time)*** 

```bash
curl --location 'http://127.0.0.1:8080/analytics/<YOUR-SHORT-KEY>'
```
Replace <YOUR-SHORT-KEY> with the short key. If the short key doesn't exist, all analytics values returned are zero. 

Returns: The amount of times the short url was called in the last 24 hours, the last week, and all time. 


**Teardown**

To stop the docker containers, you can run ```docker-compose down```, however the data stored in the local mongo instance will still persist. If you want to completely tear down the services and get rid of the data, run ```docker-compose down -v```

## Assumptions, Technical Decisions & Analysis 

URL's will be permanent, and eventually the service will have millions of users. An extremely optimistic assumption for the service can be 50 million short url's being created per year. This results in approximately 2 url writes per second(rounding up). Reads which redirecting short url's to long urls are expected the be much greater than writes; 10x perhaps. This means that there will be 500 million writes per year which approximates to 20 writes per second(2*10). This service would need to be scalable, and would have multiple services which generate short urls and access relative long urls as the application scales.

**Terms**:  

Short Key:part of the short url which appears after 'http://{domain}/' where the {domain} is the domain of our service. When the user puts in http://{domain}/{short-key}, the user will be guided to the long url that is associated with the Short key.  

### Picking the Database and schema ### 
When deciding between a relational or a NoSQL database to store the url mappings and analytics, I chose a NoSQL database. The core functionality is transforming a long url to a short url, and allowing redirection from the short url to the long url upon a request to the short url. URL mappings do not have any relationships between any other url mappings, and the database needs to be horizontally scalable and be able to perform reads quickly. For this reason a NoSQL database was picked, and Mongo was chosen in particular. Since the service is read heavy, Mongo was an ideal choice due to how it handles read operations. Unlike Cassanda, Riak, and DynamoDB, Mongo's single-leader setup allows for faster and more reliable reads. Writes also go through the leader.

For Simplicty, all data was stored in a single Mongo database, however the data was seperated by collecitons. There were three collections used for this POC:

1. url_mappings:
  This colleciton stores url mappings from the short ul to the long url. Each in Mongo is in the form  of ```{_id: <SHORT-KEY>, long_url: <LONG-URL>, timestamp <UNIX-TIMESTAMP>}```. Each mapping is a 'mongo document' within the 'url_mappings' collection. The _id field for the Mongo document is the Short key for the url. This is used to identify the document within the collection, and since the Short Key's are unique, they served as a valid _id. Mongo also automatically indexes documents based on the '_id' property. The 'long_url' field is the long url. 

2. counter
  This collection holds a single counter which is used to ensure that each service which is spun up created unique keys. How this counter is used is explained in the 'Key uniqueness' section below. This is in the form ```{_id(Object_Id), name:<COUNTER-NAME>, value: <COUNTER-VALUE>}```. This is a single mongo document within it's own 'counter' collection. The important field is the 'value' field which actually stores the value of the counter.

3. analytics
   This collection holds a mongo document in the form of {_id: <SHORT-URL>, access_times<ACCESS-TIMES>}. The _id field is the Short Key of the short url, 







### Key uniqueness and Non-guessability ###



### Making reads faster ###


### General Architecture ###





