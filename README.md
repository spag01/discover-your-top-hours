# Discover Your Top Hours

Our project identifies the most distracting and productive hours of the data using your browser history.

## Table of Contents

- [Discover Your Top Hours](#discover-your-top-hours)
  - [Table of Contents](#table-of-contents)
  - [0. Operating System Requirements](#0-operating-system-requirements)
  - [1. Extract your Browser's Database](#1-extract-your-browsers-database)
    - [Chrome](#chrome)
    - [Safari](#safari)
    - [It didn't work](#it-didnt-work)
  - [2. To generate the top 50 website](#2-to-generate-the-top-50-website)
  - [3. To generate the plots and analyze your productivity](#3-to-generate-the-plots-and-analyze-your-productivity)


## 0. Operating System Requirements

You need to ensure you have the following libraries install:

```
pandas
numpy
sqlite3
matplotlib
seaborn
zoneinfo
```

To install the [`sqlite3`](https://www.sqlite.org/) library, you may need to install `sqlite3` in your operating system.

## 1. Extract your Browser's Database

In order to analyze your data, we must first extract your browser's history.

**Note**: it is important that you upload Chrome history databases as `.sqlite3` and Safari history databases as `.db`.
This is because the browsers store the browsering history differently and need different SQL queries to interact with them.

### Chrome

**Windows**

1. Locate the history.sqlite file: 
   - `cd "%LocalAppData%\Google\Chrome\User Data\Default"` or
   - `cd "~\AppData\Local\Google\Chrome\User Data\Default"`

2. Copy the file to another location or directly used the command in step2:
   - `cp ".\History" "~\Downloads\MY_NAME.sqlite3"`


**Mac**

1. Locate the history.db file:
   - `cd ~/Library/Application\ Support/Google/Chrome/Default/` or
   - `cd "/Users/{id}/Library/Application Support/Google/Chrome/Default/"`

2. Copy the file to another location or directly used the command in step2:
   - `cp ".\History" "~\Downloads\MY_NAME.sqlite3"`

Note: it is important that you upload Chrome history databases as `.sqlite3` (see above).

### Safari

 1. Locate the history.db file:
       - `~/Library/Safari/`
       -  Or go to Finder and press `Cmd+SHIFT+G` and paste the path `~/Library/Safari/`

 2. Copy the `History.db` file to the `data` directory of this project
       - `cp ".\History" "~\Downloads\MY_NAME.db"`

Note: it is important that you upload Safari history databases as `.db` (see above).

### It didn't work

If the following steps did not work, I would suggest looking at:

 1. https://gist.github.com/dropmeaword/9372cbeb29e8390521c2
 2. https://superuser.com/a/602274

## 2. To generate the top 50 website

Run the following command:

```shell
python3 clean-scripts/get-top-50-websites.py [DATABASE FILE] [OUTPUT FOLDER] [NAME OF PERSON]
```

Example:

```shell
python3 clean-scripts/get-top-50-websites.py data/history--2022-11-25--Akshita-Safari.db output Akshita
```


## 3. To generate the plots and analyze your productivity

Runing the following command:

```shell
python3 ./clean-scripts/2-create-plots.py [DATABASE FILE] [OUTPUT FOLDER] [RATING FILE] [START DATE] [USER_TIMEZONE_STRING='US/Pacific']
```

Example:

```shell
python3 ./clean-scripts/2-create-plots.py data/Nathan_History.sqlite3 output/graphs rated-output/my_ratings.csv 2022-09-19 US/Pacific
```