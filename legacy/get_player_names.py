# opens player_dict.csv and returns first and last name of players
import pandas

df = pandas.read_csv('player_dict.csv')
first_names = df['player_firstname'].values
last_names = df['player_lastname'].values

player_names = [f + ' ' + l for f, l in zip(first_names, last_names)]

with open('player_names.txt', 'w') as f:
    for p in player_names:
        f.write(p + '\n')



