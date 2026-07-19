# Files

- contracts_competition.pkl
- hockey_scouting_notes.csv
- identity_card_0.tsv
- identity_card_1.csv
- medical_information.xlsx
- moms_notes.json
- performance.tsv

## contracts_competition.pkl (10k rows, 8 cols)

- international_id: 1-10000 (unique)
- contracts_signed: 1-17
- salary: ~124k - 18M (float), mostly <300k, probably yearly $/€
- captain: bool, 15% true
- won_championship: bool, 10% true
- jersey_number: 1-99, mostly <10
- draft_year: 2008-2025 + some outliers like 1850
- number_of_previous_teams: 0 - 15

## hockey_scouting_notes.csv (10k rows, 7 cols)

- international_id: 1-10000 (unique)
- position: str (5 options)
- dominant_hand: str (left/right), 7% missing
- experience_level: str, 4 options (veteran, rookie, sophomore, legend)
- years_played: 0-15 (0 overrepresented, default value?)
- years_pro: 0-10 (0 overrepresented)
- scout_notes: str, 10% missing

## identity_card_0.tsv (888 rows, 8 cols) is in latin, 0% missing

- numerus_internationalis_ad_identitatem: international_id in roman but too many M
- numerus_identificationis_ad_medicinam: medical_id str
- praenomen: str (first name)
- cognomen: str (family name)
- sexus: str (female, f, male, m, other)
- aetas_annorum: age 18-..., 12 entries >200
- urbs_natalis: str city (case bad)
- natio: str country (case bad)

## identity_card_1.csv (9112 rows, 8 cols)

- international_id: 1-10000 (unique but 900 missing)
- medical_id: str
- first_name
- last_name
- gender: (male, m, female, f, other)
- age: 18-..., max 455
- birth_city: str
- nationality: str country

## medical_information.xlsx (10.002 rows, 11 cols), column names in data

- medical_id
- height: num but includes (cm / m)
- weight: sometimes includes "kg"
- age_in_years
- shoe_size
- body_fat_percentage: sometimes "%"
- fitness_level: str of 12 distinct values, case bad
- sprint_time
- medical_information: list of str, example: {lower back pain, hip injury}
- return_date: various date formats
- physician_signature: str (8 distinct), weird values

## moms_notes.json (10k rows, 13 cols)

- first_name
- last_name
- age: max 455
- birth_city: bad case
- school_grade: 1 - 3.92, javascript fract {1.70000000000002}
- years_in_usa: 0-22
- eye_color: str, bad case, 16 distinct
- stuffed_animal_name: str
- favourite_board_game: str
- personal_notes: str
- favourite_child_info: 1 distinct xD
- favourite_tv_show: empty
- favourite_food: empty

## performance.tsv (10k rows, 29 cols), all nums, look good

- international_id
- goals
- assists
- num_of_shots
- shot_speed
- shot_attempts
- shooting_percentage
- high_danger_shots
- medium_danger_shots
- low_danger_shots
- save_percentage
- winning_goals
- power_play_time
- power_play_goals
- time_on_ice
- faceoff_win_percentage
- puck_touches
- puck_recoveries
- puck_possession_time
- penalty_kill_time
- penality_minutes
- penalties_taken
- time_between_penalties
- goals_against_total
- goals_against_average: 0 default?
- passes_attempted: 0 default?
- passes_completed
- pass_completion_rate
- games_missed_due_to_injury