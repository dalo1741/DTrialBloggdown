---
categories:
- Data basic
- 
date: "2021-02-28"
description: 
  Sumarize data in R
draft: false
tags:
- Excel
- R-studio
- Pivot
-
title: Be faster with R 
---

Group and sum large datasets faster with R than with pivot excel.
=======

Working with bookeeping/accoutning/auditing a common feature is to use excel as the go to tool. Nothing wrong with that excel is awesome since it´s easy. However some limitation in excel is the data it can process easily (even R have limitations.). However with that said working with for instance Journal Entries or eqvivalent and one wants to sum things up this is a useful script I use to speed this up. 
Please note that this 

Start by loading the useful packages, where tidyverse is one of the mostuseful packages for all type of data transformation/visualization
```js
library(tidyverse)
library(readr)
library(readxl)
```
Load the datafile in this case the data is sitting in the folder download and I want the sheet "Quarter"
```js
library(readxl)
> data <- read_excel("~/Downloads/MassiveDataFile.xlsx", 
+     sheet = "Quarter")
```


Then name your data set and performed the desired sumarization, please note this is generic naming of the variables
dataset = represent the file
columns in file dataset = GL/account, Currency, AMOUNT
```js
  data <- dataset %>% group_by(GL/acocunt, Currency) %>% 
        summarized(AMOUNT = sum(AMOUNT))
```
When above data set is summarized by account and currency export it into .csv with the following.

```js
  write.csv(data, "data.csv")
```
Use getwd() to if you have forgotten what is set as your directory
```js
getwd()
```


