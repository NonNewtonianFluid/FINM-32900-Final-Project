"""Run or update the project. This file uses the `doit` Python package. It works
like a Makefile, but is Python-based
"""
import sys
sys.path.insert(1, './src/')


import config
from pathlib import Path
from doit.tools import run_once


OUTPUT_DIR = Path(config.OUTPUT_DIR)
DATA_DIR = Path(config.DATA_DIR)

# fmt: off
## Helper functions for automatic execution of Jupyter notebooks
def jupyter_execute_notebook(notebook):
    return f"jupyter nbconvert --execute --to notebook --ClearMetadataPreprocessor.enabled=True --inplace ./src/{notebook}.ipynb"
def jupyter_to_html(notebook, output_dir=OUTPUT_DIR):
    return f"jupyter nbconvert --to html --output-dir={output_dir} ./src/{notebook}.ipynb"
def jupyter_to_md(notebook, output_dir=OUTPUT_DIR):
    """Requires jupytext"""
    return f"jupytext --to markdown --output-dir={output_dir} ./src/{notebook}.ipynb"
def jupyter_to_python(notebook, build_dir):
    """Convert a notebook to a python script"""
    return f"jupyter nbconvert --to python ./src/{notebook}.ipynb --output _{notebook}.py --output-dir {build_dir}"
def jupyter_clear_output(notebook):
    return f"jupyter nbconvert --ClearOutputPreprocessor.enabled=True --ClearMetadataPreprocessor.enabled=True --inplace ./src/{notebook}.ipynb"
# fmt: on


def task_pull_trace():
    """ """
    file_dep = ["./src/load_trace.py","./data/manual/cusips.csv"]
    file_output = ["fisd.csv","Prices.csv.gzip","Volumes.csv.gzip","Illiq.csv.gzip"]
    targets = [DATA_DIR / "pulled" / file for file in file_output]

    return {
        "actions": [
            "ipython ./src/load_trace.py",
        ],
        "targets": targets,
        "file_dep": file_dep,
        "clean": True,
    }

def task_pull_rating():
    '''
    Pull the ratings data from WRDS
    '''
    file_dep = ["./src/load_rating.py"]
    file_output = ["rating.csv"]
    targets = [DATA_DIR / "pulled" / file for file in file_output]

    return {
        "actions": [
            "ipython ./src/load_rating.py",
        ],
        "targets": targets,
        "file_dep": file_dep,
        "clean": True,
    }

def task_pull_return_cs():
    '''
    pull daily return and credit spread data from Open Bond Asset Pricing website.
    '''
    file_dep = ["./src/load_return_cs.py"]
    file_output = ["BondDailyPublic.csv.gzip"]
    targets = [DATA_DIR / "pulled" / file for file in file_output]

    return {
        "actions": [
            "ipython ./src/load_return_cs.py",
        ],
        "targets": targets,
        "file_dep": file_dep,
        "clean": True,
    }

def task_calc_spread_bias():
    '''
    Calculate spread and bias
    '''
    file_input = ['Illiq.csv.gzip', 'rating.csv']
    file_dep = ["./src/calc_spread_bias.py"] + [DATA_DIR / "pulled" / file for file in file_input]
    
    file_output = ["spread_bias.csv"]
    targets = [DATA_DIR / "pulled" / file for file in file_output]

    task_dep = ["pull_trace","pull_rating"]

    return {
        "actions": [
            "ipython ./src/calc_spread_bias.py",
        ],
        "targets": targets,
        "task_dep": task_dep,
        "file_dep": file_dep,
        "clean": True,
    }


def task_calc_daily_return_cs():
    '''
    calculate daily return and credit spread, with filtering conditions
    '''
    file_input = ['BondDailyPublic.csv.gzip']
    file_dep = ["./src/calc_daily_return_cs.py"] + [DATA_DIR / "pulled" / file for file in file_input]
    
    file_output = ["daily_return_cs.csv"]
    targets = [DATA_DIR / "pulled" / file for file in file_output]

    task_dep = ["pull_return_cs"]

    return {
        "actions": [
            "ipython ./src/calc_daily_return_cs.py",
        ],
        "targets": targets,
        "task_dep": task_dep,
        "file_dep": file_dep,
        "clean": True,
    }



def task_summary_stats():
    """ """
    file_input = ['spread_bias.csv', 'daily_return_cs.csv','rating.csv']
    file_dep = ["./src/derive_table.py"] + [DATA_DIR / "pulled" / file for file in file_input]

    file_output = ["derive_table.tex"]
    targets = [OUTPUT_DIR / file for file in file_output]

    return {
        "actions": [
            "ipython ./src/derive_table.py",
        ],
        "targets": targets,
        "file_dep": file_dep,
        "clean": True,
    }



def task_convert_notebooks_to_scripts():
    """Preps the notebooks for presentation format.
    Execute notebooks with summary stats and plots and remove metadata.
    """
    build_dir = Path(OUTPUT_DIR)
    build_dir.mkdir(parents=True, exist_ok=True)

    notebooks = [
        "01_intraday_daily.ipynb",
        "03_summary_stats.ipynb"
    ]
    file_dep = [Path("./src") / file for file in notebooks]
    stems = [notebook.split(".")[0] for notebook in notebooks]
    targets = [build_dir / f"_{stem}.py" for stem in stems]

    actions = [
        # *[jupyter_execute_notebook(notebook) for notebook in notebooks_to_run],
        # *[jupyter_to_html(notebook) for notebook in notebooks_to_run],
        *[jupyter_clear_output(notebook) for notebook in stems],
        *[jupyter_to_python(notebook, build_dir) for notebook in stems],
    ]
    return {
        "actions": actions,
        "targets": targets,
        "task_dep": [],
        "file_dep": file_dep,
        "clean": True,
    }


def task_run_notebooks():
    """Preps the notebooks for presentation format.
    Execute notebooks with summary stats and plots and remove metadata.
    """
    notebooks = [
        "01_intraday_daily.ipynb",
        "03_summary_stats.ipynb"
    ]
    stems = [notebook.split(".")[0] for notebook in notebooks]
    fig_names = ["spread_categorized", "winsorized_bias_categorized", "daily_return_bps_categorized",
                 "cs_dur_bps_categorized", "rating", "rating_cleaned"]

    file_dep = [
        # 'load_other_data.py',
        *[Path(OUTPUT_DIR) / f"_{stem}.py" for stem in stems],
    ]

    targets = [
        ## 03_summary_stats.ipynb output
        OUTPUT_DIR / "summary_stats.tex",
        *[OUTPUT_DIR / f"{fig_name}.png" for fig_name in fig_names],
        ## Notebooks converted to HTML
        *[OUTPUT_DIR / f"{stem}.html" for stem in stems],
    ]

    actions = [
        *[jupyter_execute_notebook(notebook) for notebook in stems],
        *[jupyter_to_html(notebook) for notebook in stems],
        *[jupyter_clear_output(notebook) for notebook in stems],
        # *[jupyter_to_python(notebook, build_dir) for notebook in notebooks_to_run],
    ]
    return {
        "actions": actions,
        "targets": targets,
        "task_dep": [],
        "file_dep": file_dep,
        "clean": True,
    }



def task_compile_latex_docs():
    """Example plots"""
    file_dep = [
        "./reports/report_example.tex",
        # "./src/example_plot.py",
        # "./src/example_table.py",
    ]
    file_output = [
        "./reports/report_example.pdf",
    ]
    targets = [file for file in file_output]

    return {
        "actions": [
            "latexmk -xelatex -cd ./reports/report_example.tex",  # Compile
            "latexmk -xelatex -c -cd ./reports/report_example.tex",  # Clean
        ],
        "targets": targets,
        "file_dep": file_dep,
        "clean": True,
    }
