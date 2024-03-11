# URL-Shortener

## Overview

This project serves as a proof of concept (POC) for a service which allows a user to transform lengthy URLs into short URL's similar to [bit.ly](https://bitly.com/). This project follows a design and architecture aiming to minimize problems as the service scales to millions of users. 

## How to test

**Prerequisites**
Please ensure you have Docker Desktop on your machine and can access docker commands from the cli

**Setup and testing**
To setup the service, please do the following:

Go into the ```backend``` folder of the project and run 
```bash 
docker-compose up -d --build --scale flask-backend=<NUMBER-OF-SERVICES>
```
Replace ```<NUMBER-OF-SERVICES>``` with a value greater than 1. This will specify how many flask servers will be run. 

The flask api will now be accessible at port 80 of your local machine or http://127.0.0.1:80 

The api allows three calls:

***1. Setting a short url for a long url. The following curl returns a short url.***

  ```bash
curl --location 'http://127.0.0.1:80/shorten' \
--header 'Content-Type: application/json' \
--data '  {
    "long_url": "<YOUR-LONG-URL>",
    "back_half": "<YOUR-BACK-HALF>"
  }'

```
In the data section:

```long_url```: The long url you want to shorten.  

```back_half(optional)```: This is a custom short key that the user can provide. If the key has not already been used, the end of the url after the domain will be this key. If this field is empty or not provided, then a unique key     will automatically be created for the user.

Returns: A short url. 

***2. Getting a long url from a short url***

  ```bash
  curl --location 'http://127.0.0.1:80/<YOUR-CUSTOM-KEY>'
  ```
  Replace ```<YOUR-CUSTOM-KEY>``` with the short key you want to find. 
  
  Returns: the webpage that the long url for the short key links to. 
     
***3. Getting the analytics of a short url (how many times it was accessed in the last 24 hours, week, and all time)*** 

  ```bash
  curl --location 'http://127.0.0.1:80/analytics/<YOUR-SHORT-KEY>'
  ```
  Replace ```<YOUR-SHORT-KEY>``` with the short key. If the short key doesn't exist, all analytics values returned are zero.  
  
  Returns: The amount of times the short url was called in the last 24 hours, the last week, and all time. 


**Unit tests**: To execute unit tests, run the following commands in order from directory of this project
```bash
source bin/activate
pip3 install -r requirements.txt
pytest
```

**Teardown**

To stop the docker containers, you can run ```docker-compose down```, however the data stored in mongo will persist. If you want to completely tear down the services and get rid of the data, run ```docker-compose down -v```

## Assumptions, Technical Decisions & Analysis 

URL's will be permanent, and eventually the service will have millions of users. An extremely optimistic assumption for the service can be 50 million short url's being created per year. This results in approximately 2 url writes per second(rounding up). Reads which involve redirecting short url's to long urls are expected the be much greater than writes; 10x perhaps. This means that there will be 500 million reads per year which approximates to 20 writes per second. This service would need to be scalable, and would have multiple services which generate short urls and access relative long urls as the application scales.

**Terms**:  

Short Key: part of the short url which appears after 'http://{domain}/' where the {domain} is the domain of our service. When the user puts in http://{domain}/{short-key}, the user will be guided to the long url that is associated with the Short key.  

### Picking the Database and schema ### 
When deciding between a relational or a NoSQL database to store the url mappings and analytics, I chose a NoSQL database. The core functionality is transforming a long url to a short url, and allowing redirection from the short url to the long url upon a request to the short url. There are no relationships between URL mappings, and the database needs to be horizontally scalable and be able to perform reads quickly. For this reason a NoSQL database was picked, and Mongo was chosen in particular. Since the service is read heavy, Mongo was an ideal choice due to how it handles read operations. Unlike Cassanda, Riak, and DynamoDB, Mongo's single-leader setup allows for faster and more reliable reads. Writes also go through the leader.

For Simplicty, all data was stored in a single Mongo database, however the data was seperated by collecitons. There were three collections used for this POC:

Note: A Mongo document is basically a record in MongoDB represented as a data structure composed of field and value pairs. 

1. url_mappings:  
  This colleciton stores url mappings which map the short url to the long url. Each document represents a mapping in the form: ```{_id: <SHORT-KEY>, long_url: <LONG-URL>, timestamp <UNIX-TIMESTAMP>}```. This is a 'mongo document' within the 'url_mappings' collection. The _id field for the document is the Short key for the url. This is used to identify the document within the collection, and since the Short Key's are unique, they served as a valid '_id'. Mongo automatically indexes documents based on the '_id' property. The 'long_url' field is the long url. 

2. counter:  
  This collection holds a single counter which is used to ensure that each service which is spun up creates different keys. How this counter is used is explained in the 'Key uniqueness' section below. This is in the form ```{_id(Object_Id), name:<COUNTER-NAME>, value: <COUNTER-VALUE>}```. This is a single mongo document within it's own 'counter' collection. The important field is the 'value' field which actually stores the value of the counter.

4. analytics:  
   This collection holds mongo documents in the form of ```{_id: <SHORT-URL>, access_times<ACCESS-TIMES>}```. The _id field is the Short Key of the short url, and the 'access_times' is an array of unix timestamps in ascending order that the short url(key) was accessed. Each time the short url is accessed, the latest timestamp is appended to the end of the access_times array.


### Key uniqueness and Non-guessability ###

Short Key size: The short key size for this implementation will be in the range of 5-8 characters long. 8 characters will be the largest short key size our service will allow because the short url should still be small. The reason for these ranges is explained below. 

The characters used for the short key are base62(a-z, A-Z, 0-9) because this is a large character set to choose from and the keys formed using these characters will not have issues with a browser. The reason I avoided base 64 was because the '+' and the '/' characters which would need to be encoded as ‘%2B’ and ‘%2F’ respectively. There is no big benefit of using base64 over base62 for our case. There were multiple ways that the unique keys could have been created. Some of the solutions I was looking at were:
* Get a MD5 of the long url which produces a 128-bit hash value. This value would be converted to base62 and the first/last n characters would be used as the short key. This becomes a problem when different users input the same long url as they will get the same short key. 
* Generate a random key of size n with base62 characters. This can cause collisions on write, and there is no direct way to reduce the probability of impacts. Additionally as the service gets many more short url creations, the probabilty of collisions increases. This puts additional burden on the system to find a short key which is not present in the database. This solution could work well with a seperate Key Generation service and database which stores used and unused(unique) keys ahead of time allowing our service to simply pick an unused key on short url creation. 


**Chosen Solution:** There is a counter in the data store that each service reads and increments by a set value (10000 in our case) per database transaction. Upon successfully committing the transaction, a service can use the range of counter values it reserved (from the initial read value up to the read value plus the increment minus one) to generate short URLs. This ensures that each service has a unique set of counter values to use for URL generation, effectively preventing conflicts between servers. However, there's a risk of losing up to 10000 short URLs if a service crashes after reserving its range but before using all the values. With that being said, this method is still viable due to the vast number of short URLs (up to 57 billion) that can be generated. At the peak write load of 5,000,000 key generations per year, it would take about 11,400 (57 billion/5 million) years to use up the unique base62 keys which are used as the prefix for the short key. With Mongo, writes are atomic at the level of a single document which helps us ensure that only one process at a time can access this global counter (in the code, the counter is incremented by 10000 automatically whenever it is read by a service), so that two or more processes at the same time do not take on the same counter ranges. 

To avoid the guessability of short urls created before/after a given short url, two random base62 characters are added to the base62 transformation of the counter value. The smallest size for a key can be five characters (10000 in base62 is 2Bi + two random base62 characters), and the largest size that we would allow can be 8 (a base62 number of size 6 + two random base62 characters). On each short key creation, the conversion of the integer counter to base62 will always yield a unique value, however adding the random two characters at the end might cause a collision. For this reason it is still be important to check if the generated short key is already in the database before mapping it to a long url.  



### Making reads faster ###

Because of the high number of reads(url redirections) that our service will encounter, it is important that reads are very efficient. Here are some of the methods implemented to speed up reads. 

**NoSQL**:Using a NoSQL database like Mongo helps with performance and speed. Mongo offers efficient lookups by document identifier, it is designed for high throughput, and has built in sharding capabilites. 

**Cache**: To speed up read requests, an in-memory cache was added. Redis was used for the cache. In terms of whether this cache would be local to each service, or global so that all services could access the cache; the decision to go with the global cache was made. The reason for this is because load-balancing could be random, round-robin, or traffic based (Where load will be redirected to less busy servers). If the same short url is searched for, different services could end up handling these URL redirection requests which would result in extra trips to the db.

**Analytics**: One of the requirements of this poc was to get usage analytics for each short url over the last 24hrs, last week, and all time. To save time on the analytics read, I am using the fact that the array of access timestamps is sorted and doing a binary seach to find the analytics values. On each read, an analytics write occurs where the timestamp is added to the mongo document identified by the short key. The request would complete when the access timestamp is written to the database. I decided to spin up a new thread to do this write for simplicity and for the fact that this thread would be concurrent with the url redirection (resources are still used with the thread creation). As this service scales to millions of requests, it would be important to create a seperate analytics service and put the analytics writes into a queing system like RabbitMQ or Kafka. With analytics, we can have eventual consistency, and this analytics service could be a seperate process that reads messages from the queue and updates the analytics database. This analytics service can be run at set time periods (every hour perhaps).

**Load Balancing**: Nginx was used as the load balancer for the flask services due to Nginx's easy setup. The load-balancer prioritizes load to servers which are receiving less load. This helps prevent busy servers from becoming the bottlneck for requests. 



### Potential Bottlenecks ###
**Analytics**:   
* Threads: Currently each write to the analytics collection happens in a new thread. With millions of requests, threads will become a bottleneck because of the amount of resources(CPU, memory) that the threads will collectively take up. This is where a service like RabbitMQ and a seperate analytics processing service as described above will become important. 

* Storage of Analytics: Each short url redirection timestamp is appended to an array within a mongo document identified by the short key. In Mongo the max size of a document is 16MB so for more frequently accessed url's this document could fill up fast. There could be an additional services which is responsible for compressing these arrays (where timestamps older than a week are collapsed but there is still a count of all the collapsed timestamps.), but this can become very inefficient if done constantly with MongoDB and can slow down the database. I personally think in this scenario, the best option would be to use a time-series database such as InfluxDB or Splunk because they have their own efficient compression techniques, and manage range queries efficiently (Just learned about these an hour ago).  



