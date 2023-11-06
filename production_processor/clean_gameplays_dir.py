import os.path

from config.config import path_root
from library.tools import clean_unfinished_gameplays, get_project_root, rename_gameplays

clean_unfinished_gameplays(os.path.join(get_project_root(), "gameplays"))
# clean_unfinished_gameplays(os.path.join("D:\\Uniwersytet Jagielloński\\StoryGraph - General\\logi z rozgrywek", "gameplays"))

# rename_gameplays(os.path.join(get_project_root(), "gameplays"))
# rename_gameplays(os.path.join("D:\\Uniwersytet Jagielloński\\StoryGraph - General\\logi z rozgrywek\\gameplays", "2023_03-teraz (z diagramami)"))
