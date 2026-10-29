"""Fixed source snapshots and measurement contrasts; no fitted model."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
YEARS=[2019,2021,2023]
DEV_YEARS=[2019,2021]
EVAL_YEARS=[2023]
DENOMS=['population','licensed_drivers','vmt_millions']
GROUPS=['all','motorcyclists','pedestrians','pedalcyclists']
SHARES=['drivers','passengers','motorcyclists','pedestrians','pedalcyclists']
REPORTS={2019:'813183',2021:'813509',2023:'813743'}
STATES=['Alabama','Alaska','Arizona','Arkansas','California','Colorado','Connecticut','Delaware','District of Columbia','Florida','Georgia','Hawaii','Idaho','Illinois','Indiana','Iowa','Kansas','Kentucky','Louisiana','Maine','Maryland','Massachusetts','Michigan','Minnesota','Mississippi','Missouri','Montana','Nebraska','Nevada','New Hampshire','New Jersey','New Mexico','New York','North Carolina','North Dakota','Ohio','Oklahoma','Oregon','Pennsylvania','Rhode Island','South Carolina','South Dakota','Tennessee','Texas','Utah','Vermont','Virginia','Washington','West Virginia','Wisconsin','Wyoming']
