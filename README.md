# Stable Diffusion Database Manager

![Project logo](README_images/stable-diffusion-database-manager-logo.png)  
## Table of Contents

- [Introduction](#introduction)
- [Usage](#usage)
- [Test](#test)
- [Known Issues](#known-issues)

## Introduction

Stable Diffusion Database Manager named Nex is a Stable Diffusion extension.  
It supports generating of a single or in batches of images that will be inserted into a single or multiple databases.  
The extension is built using the existing stable diffusion webUI gradio UI framework.   

It supports 4 different types of databases such as:
1. MySQL (RDBMS, SQL)
1. Postgres (RDBMS, SQL)
1. Neo4j + IPFS (Graph, CQL)
1. MongoDB (Document, NoSQL)
1. SQlite

### Use Cases

Beneficial for producing images intended for distribution across diverse platforms.  
This approach is especially effective for content that demands intricate post-processing tasks, including label categorization, advanced image enhancement, and beyond.

Another use case could be distributed systems of image backup.  
Suggest to use neo4j + IPFS for such case, since IPFS is known for high availability and its distribution capabilities in a public network of nodes.

### MySQL Demonstration Screenshot

![MySQL Demonstration Screenshot](README_images/stable-diffusion-database-manager-2.png)   

### PostgreSQL Demonstration Screenshot

![PostgreSQL Demonstration Screenshot](README_images/stable-diffusion-database-manager-3.png)   

### Neo4J + IPFS Demonstration Screenshot

![Neo4J + IPFS Demonstration Screenshot](README_images/stable-diffusion-database-manager-4.png)   

### MongoDB Demonstration Screenshot

![MongoDB Demonstration Screenshot](README_images/stable-diffusion-database-manager-5.png)   

### SQlite Demonstration Screenshot

![SQlite Demonstration Screenshot](README_images/stable-diffusion-database-manager-6.png)   

## Usage

### Required Installation

1. Install stable-diffusion (https://github.com/AUTOMATIC1111/stable-diffusion-webui)
1. Install Docker v4.22.0 or higher (https://docs.docker.com/engine/install)
1. Install Python 3.10.6 (tags/v3.10.6:9c7b4bd) (https://www.python.org/downloads/release/python-3106/)
1. Install Git (https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

### Stable Diffusion WebUI (Recommended)

If you are using [Stable Diffusion WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui) 

1. Start Stable Diffusion WebUI (https://github.com/AUTOMATIC1111/stable-diffusion-webui#installation-and-running)
1. Go to extensions tab
1. Go to Install from URL tab
1. Copy this github link and paste into (URL for extension's git repository)
1. Press install
1. Restart Stable Diffusion WebUI

Alternatively, is to git clone or download this repository and place everything into the stable diffusion webUI ``extensions`` folder


### Using the extension


![Introductory image](README_images/stable-diffusion-database-manager-1.png) <!-- Replace with your introductory image -->

1. Go to Settings tab  
1. Find for Nex databases within Uncategorized section  
1. When setting up and enabling one or more databases  
1. Always save your changes by hitting the button **Apply Settings**  
1. Check the connection String and ensure the database schema is created.  
1. Test connectivity button to ensure extension is able to connect with the respective database.  
1. Tables, columns, and collections are created on the fly if they do ``not exist`` in the 1. database when images are generated.  

Refer to **Test and Adminer UI** to access the various database types to create a database.

## Test

This project has been developed and tested in Windows using docker containers for ease of setup and configuration.  

Docker will install various images, docker networks, and setup containers such as:  
1. MySQL 5.7
1. PostgresSQL latest
1. Mongodb latest
1. Mongo express, access MongoDB web based database UI at (http://localhost:8081/) 
1. Adminer, access MySQL and PostgresSQL Web based Database UI at (http://127.0.0.1:8085/)
1. Neo4j latest, access neo4j UI at (http://127.0.0.1:7474)
1. IPFS 0.7.0, access IPFS UI at (http://127.0.0.1:5001/webui/)
---
Run the test by executing docker-compose
```
cd scripts/test
```
```
docker-compose up -d
```
The above command will download and install all relevant docker containers  

The credentials **(username and password)** can be found at ``scripts/test/docker-compose.yml``

Please change and secure the credentials.

**When using Adminer UI**  

The default username for MySql is **root**  
The default username for PostgreSql is **postgres**  

For Windows and Mac  
The **Server** input box will be: ``host.docker.internal``  

For Linux  
Run the command ```ip route | awk 'NR==1 {print $3}'```  
Copy the ip address and paste it into the **Server** input box  

**Testing SQLite**  
Use any Sqlite tools to view the sqlite db file.  
https://inloop.github.io/sqlite-viewer/ is a good start.  

## Known Issues

- Issue 1: Neo4j and IPFS are using IPFS ipfs/go-ipfs:v0.7.0, the python client for IPFS only supports up to that version.
- Issue 2: Neo4j is hardcoded for both named Prompt and Images when creating a new node.

---

Feel free to contribute to this project by submitting issues or pull requests.