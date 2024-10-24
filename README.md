# Rake: Configure and Scrape

Rake is a simple yet powerful web scraping tool that allows you to configure and execute complex and repetitive scraping tasks with ease and little to no code.

## Table of Contents

1. [Introduction](#introduction)
2. [Features](#features)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Configuration](#configurations)
6. [Data Transformation](#data-transformation)
7. [Output Formats](#output-formats)
8. [Advanced Features](#advanced-features)
9. [Troubleshooting](#troubleshooting)
10. [Contributing](#contributing)
11. [License](#license)

## Introduction

Rake is designed to simplify the process of web scraping by providing a configuration-based approach. It allows users to define scraping tasks using YAML files, making it easy to specify selectors, interactions, and data extraction rules without writing complex code.

## Features

- **YAML Configuration**: Define scraping tasks using simple and readable YAML files.
- **Flexible Selectors**: Use CSS selectors to target specific elements on web pages.
- **Interactive Scraping**: Perform clicks, form submissions, and other interactions during the scraping process.
- **Pagination Support**: Easily navigate through multiple pages of content.
- **Data Extraction**: Extract text, attributes, and custom data from web pages.
- **Variable Support**: Use variables to store and reuse data across different scraping steps.
- **Data Transformation**: Apply custom transformations to extracted data using Python functions.
- **Multiple Output Formats**: Export scraped data in various formats, including JSON and Excel.
<!-- - **Resumable Scraping**: Ability to pause and resume scraping tasks. -->

## Installation

```
pip install rake-scraper
```

This will install Rake and all its dependencies.

## Usage

### CLI

1. Create a YAML configuration file defining your scraping task.

```
# example.com.yaml

logging: true
output:
  name: example.com
  path: outputs/
  formats:
    - json
    - yaml

rake:
  - link: https://example.com
    interact:
      nodes:
        - selector: body
          data:
            - scope: data
              value:
                title: $attr{text@H1}
                description: $attr{text@P}
                more_info: $attr{href@A}

```

2. Run the Rake command-line tool, specifying your configuration file:

```
rakestart example.com.yaml
```

3. Rake will execute the scraping task and save the results according to your configuration.

### Programmatically

```
from rake import Rake

# Loads config from file into a python dict
config = Rake.load_config("example.com.yaml")

# Initialize Rake with the config
rake = Rake(config)

rake.start()
```

## Configurations

Rake uses various nested configuration options. These options define the structure and behavior of your scraping tasks. Here's an overview of the various configuration sections:

_**Note**: configuration will be written in YAML throughout this documentation, although Rake itself accepts Python dictionaries as configuration._

### Browser Settings `browser`

The `browser` configuration section allows you to customize the behavior of the browser used for scraping. Here's an overview of the available settings:

- `type` (string): Specifies the browser type to use. Options include:

  - `chromium` (default)
  - `firefox`
  - `webkit`

- `show` (boolean): Determines whether the browser window is visible during scraping.

  - `true`: Show the browser window
  - `false`: Run in headless mode (default)

- `timeout` (integer): Sets the maximum time (in milliseconds) to wait for page loads and other operations.

  - Default: 30000 (30 seconds)

- `slowdown` (integer): Adds a delay (in milliseconds) between actions to simulate human-like behavior.

  - Default: 0 (no delay)

- `ready_on` (string): Specifies when to consider a page as fully loaded. Options include:

  - `load`: Wait for the load event (default)
  - `domcontentloaded`: Wait for the DOMContentLoaded event
  - `networkidle`: Wait until there are no network connections for at least 500 ms

- `viewport` (array): Sets the browser viewport size [width, height].

  - Example: [1920, 1080]
  - Default: [1280, 720]

- `block` (array): Specifies resource types to block during page loads. Options include:
  - `document`
  - `stylesheet`
  - `image`
  - `media`
  - `font`
  - `script`
  - `texttrack`
  - `xhr`
  - `fetch`
  - `eventsource`
  - `websocket`
  - `manifest`
  - `other`

Example configuration:

```
browser:
  type: firefox
  show: true
  timeout: 120000
  slowdown: 500
  ready_on: load
  block: [image, other]
```

### Logging `logging`

The `logging` configuration option controls the verbosity of Rake's output during execution. It can be set to either `true` or `false`:

- `true`: Enables detailed logging, providing information about page openings, interactions, and other operations.
- `false`: Disables logging, resulting in minimal output (default).

Example configuration:

```
logging: true
browser:
  ...
```

### Output Settings `output`

The `output` configuration controls how and where Rake saves the scraped data. It includes the following settings:

- `path` (string): Specifies the directory where output files will be saved.

  - Example: `output/`
  - Default: Current working directory

- `name` (string): Sets the base name for output files.

  - Example: `my_scrape_results`
  - Default: `rake_output`

- `formats` (array): Defines the output file formats. Each format can be a string or an object with additional options.

  - Supported formats:
    - `yaml`
    - `json`
    - `excel`
  - Format object properties:

    - `type` (string): The format type (required)
    - `transform` (string): Name of a custom python module with a `transform` function (optional)

      ```
      # to_excel.py

      import pandas as pd

      def transform(data):
        ...
      ```

Example configuration:

```
output:
  path: outputs/
  name: example.com
  formats:
    - json
    - type: excel
      transform: to_excel # no file extension needed and must not be in a nested directory
```

### Rake Pages `rake`

The `rake` configuration defines the scraping behavior for each page. It includes A list of page configurations. Each page configuration can include:

- `link` (string or object): The URL to scrape or a link object with additional metadata.

  - Link object properties:

    - `url` (string): The URL to scrape or the name of the captured link group (e.g., `$products_page`)
    - `metadata` (object): Additional metadata that can be accessed using the `$var{category}` notation

  - Example string: `"https://example.com"` or `$products_page`
  - Example object: `{ url: "https://example.com", metadata: { category: "blog" } }`

- `interact` (object): Defines interactions with the page.

  - `repeat` (number or object): Specifies how many times or under what conditions to repeat the interactions.
    - Example number: `3`
    - Example object: `{ selector: ".load-more", disabled: false }`
  - `nodes` (array): A list of node configurations for interacting with page elements.

- `data` (object or array): Specifies what data to extract from the page.

  - `scope` (string): CSS selector to limit the data extraction scope.
  - `value` (string or object): Defines what to extract (e.g., text content, attribute value).

- `links` (object or array): Configures link extraction for further crawling.
  - `selector` (string): CSS selector for finding links.
  - `attribute` (string): Attribute to extract as the URL (default: "href").
  - `name` (string): Name for the extracted link group.

Example configuration:

```
rake:
  - link: https://example.com
    interact:
      ...
```
