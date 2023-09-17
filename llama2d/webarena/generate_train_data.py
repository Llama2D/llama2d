import json

from browser_env import ScriptBrowserEnv, create_id_based_action

from ..constants import ARENA_SAVED_DIR,SCREEN_RESOLUTION

width, height = SCREEN_RESOLUTION

def generate_web_arena_data():

    with open("webarena/config_files/test.raw.json", "r") as f:
        all_samples = json.load(f)

    # init the environment
    env = ScriptBrowserEnv(
        headless=False,
        observation_type="accessibility_tree",
        current_viewport_only=True,
        viewport_size={"width": width, "height": height},
    )

    tmp_config_file = "config.tmp.json"

    for sample in all_samples:

        with open(tmp_config_file, "w") as f:
            json.dump(sample, f)

        # prepare the environment for a configuration defined in a json file
        obs, info = env.reset(options={"config_file": tmp_config_file})
        # get the text observation (e.g., html, accessibility tree) through obs["text"]

        # create a random action
        id = random.randint(0, 1000)
        action = create_id_based_action(f"click [id]")

        # take the action
        obs, _, terminated, _, info = env.step(action)
