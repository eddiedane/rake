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
8. [License](#license)

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

err, data = rake.start()

if err:
  ...

rake.data('./outputs/example.com.json')
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

**Example configuration:**

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

**Example configuration:**

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

**Example configuration:**

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

The `rake` configuration defines the scraping behavior for each type page. It includes A list of page configurations. Each page configuration can include:

- `link` (string or object or list): The URL to scrape or a link object with additional metadata.

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

**Example configuration:**

```
rake:
  - link: https://example.com
    interact:
      ...
```

### Interactions `interact`

The `interact` configuration defines how Rake interacts with elements on the page. It can include the following settings:

- `repeat` (number or object): Specifies how many times or under what conditions to repeat the interactions.

  - Example number: `3`
  - Example object: `{ value: "disabled@.load-more-button", while: [is, false] }`

- `nodes` (array): A list of node configurations for interacting with page elements. Each node can have:

  - `selector` (string): CSS selector for the element to interact with.
  - `all` (boolean): Whether to interact with all matching elements or just the first one.
  - `show` (boolean): Whether to scroll the element into view before interacting.
  - `actions` (array): List of actions to perform on the element. Each action can be:

    - `type` (string): The type of action (e.g., "click", "swipe_left", "swipe_right").
    - `value` (string): The value to use for the action (e.g., text to type).
    - `dispatch` (boolean): Whether to dispatch the event using JavaScript.
    - `count` (number): Number of times to repeat the action.
    - `wait` (number): Milliseconds to wait after the action.
    - `delay` (number): Milliseconds to wait before the action.
    - `screenshot` (string): Path to save a screenshot before the action.

  - `links` (array): Configurations for collecting and queueing links from the element for further crawling.
  - `data` (array): Configurations for extracting data from the element.
  - `interact` (object): [Interactions](#interactions-interact)

**Example configuration:**

```
interact:
  repeat: 3
  nodes:
    - selector: .pagination-item-next-page
      wait: 1000
      actions:
        - type: click
  ...
```

### Collecting and Queueing Links `links`

The `links` configuration allows Rake to collect and queue links from the elements for further crawling. Each link configuration can include the following settings:

- `name` (string): The name to identify the collected links.
  **Example usage:**

  ```
  # add links
  link:
    - name: products_page
    ...

  # then
  rake:
    - link: $products_page
    ...
  ```

- `url` (string): The URL or a JavaScript expression to evaluate and extract the link.
- `metadata` (object): Additional metadata to associate with the collected link. Each key-value pair can be:
  - `key` (string): The name of the metadata field.
  - `value` (string): The value or a JavaScript expression to evaluate and extract the metadata.
    **Example:**
  ```
  metadata:
    category_name: '$attr{text@h1}'
    ...
  ```

**Example configuration:**

```
links:
  - name: collections
    url: $attr{href@a}
    metadata:
      id: $attr{text@span.id}
```

### Extracting Data `data`

The `data` configuration allows Rake to extract and structure data from the elements. Each data configuration can include the following settings:

- `scope` (string): The scope or path where the extracted data will be stored.
  **Example usage:**

  ```
  scope: collections
  ```

  **Example with nested object:**

  ```
  # product is an object
  scope: product.variant

  # find collection by name
  scope: collections.$key{name=$collection_name}.products
  ```

  **Example with nested object:**

- `value` (string | list | object): The value to extract. It can be a string, a list of strings, or an object with key-value pairs where each value is a string or an object.
  **Example usage:**

  ```
  value: $attr{text@h1}
  ```

  **Example with list:**

  ```
  value:
    - $attr{text@h1}
    - $attr{href@a}
  ```

  **Example with object:**

  ```
  value:
    name: $attr{text@h1}
    url: $attr{href@a}
  ```

**Example configuration:**

### Concurrency `race`

The `race` configuration option controls how many links Rake will scrape concurrently.

- `number` (integer): The number of links to scrape concurrently.
- Default value: 1 (scrape pages sequentially)

**Example:**

```
race: 5 # scrape 5 links concurrently
```

## Data Transformation

Rake allows you to apply custom data transformations to the extracted data using Python modules. This feature is useful when you need to process or clean the data before saving it to the output formats.

### Using a Custom Module

Create a Python module with a `transform` function in the root directory of your project.
Then to use the custom module for data transformation, specify the module name in the `transform` field under `output.formats`.

The transform function accepts two arguments:

- `data`: The scraped data.
- `filepath`: The path to the output file.

and return either `None` or the transformed data.

- Return `None`, tells Rake that the data has been processed and saved to file.
- Return the transformed data, tells Rake to save the data to file.

**Example:**

```
# to_excel.py

import pandas as pd

def transform(data):
  import pandas as pd

def transform(data, filepath):
  with pd.ExcelWriter(filepath) as writer:
    collections = [
      [collection.get('name'), collection.get('url'), len(collection.get('products', []))]
      for collection in data['collections']
    ]

    df = pd.DataFrame(collections, columns=['Name', 'URL', 'Products'])

    df.to_excel(writer, index=False, sheet_name='Collections')

    for collection in data['collections']:
      df = pd.DataFrame([
        [product.get('title'), product.get('url'), product.get('price'), len(product.get('variants', []))]
        for product in collection.get('products', [])
      ], columns=['Title', 'URL', 'Price', 'Variants'])

      df.to_excel(writer, index=False, sheet_name=collection.get('name'))

    return None
```

**Example:**

```
output:
  ...
  formats:
    - type: excel
      transform: to_excel
```

## Output Formats

Rake currently supports the following output formats:

- `json`
- `yaml`
- `excel`

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
