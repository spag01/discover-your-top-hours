# Use anaconda's python
source C:/Users/natha/anaconda3/Scripts/activate dataScience

# Nathan's Plots
python ./clean-scripts/2-create-plots.py \
  "data/history--2022-10-21--Nathan-Tsai.sqlite3" \
  "output/graphs" \
  "rated-output/Ratings - CMPT 353 - Nathan Tsai (1).csv" \
  2022-10-19 US/Pacific

# Juan's Plots
python ./clean-scripts/2-create-plots.py \
  "data/history--2022-10-21--Juan-Gonzalez.sqlite3" \
  "output/graphs" \
  "rated-output/Ratings - CMPT 353 - Juan Gonzalez.csv" \
  2022-09-19 US/Pacific

# Sanyam's Plots
python ./clean-scripts/2-create-plots.py \
  "data/history--2022-11-25--Sanyam-Safari.db" \
  "output/graphs" \
  "rated-output/Ratings of Inputted Users - CMPT 353 - Sanyam (2).csv" \
  2022-09-19 US/Pacific
