# Rake: Configure and Scrape

Rake is a simple yet powerful web scraping tool that allows you to configure and execute complex and repetitive scraping tasks with ease and little to no code.

## Table of Contents

1. [Introduction](#introduction)
2. [Features](#features)
3. [Installation](#installation)
4. [Usage](#usage)
   - [CLI](#cli)
   - [Programmatically](#programmatically)
5. [Configuration](#configurations)
   - [Browser Settings](#browser-settings-browser)
   - [Logging](#logging-logging)
   - [Portal](#portal-portal)
   - [Output Settings](#output-settings-output)
   - [Rake Pages](#rake-pages-rake)
   - [Interactions](#interactions-interact)
   - [Capturing and Queuing Links](#capturing-and-queueing-links-links)
   - [Extracting Data](#extracting-data-data)
   - [Concurrency](#concurrency-race)
6. [Data Transformation](#data-transformation)
7. [Portal Actions](#portal-actions)
   - [Setup using portal.py](#setup-using-portalpy)
   - [Setup using dict](#setup-using-dict)
   - [Portal Usage](#portal-usage)
8. [Output Formats](#output-formats)
9. [Special Notations](#special-notations)
   - [DOM Element Access](#dom-element-access)
   - [Variable Access](#variable-access)
   - [Combining Notations](#combining-notations)
   - [Links Name Reference](#links-name-reference)
   - [Data Scoping: Forming the structure of the data](#data-scoping-forming-the-structure-of-the-data)
10. [License](#license)

## Introduction

[&uarr; Back to Table of Contents](#table-of-contents)

Rake is designed to simplify the process of web scraping by providing a configuration-based approach. It allows users to define scraping tasks using YAML files, making it easy to specify selectors, interactions, and data extraction rules without writing complex code.

## Features

[&uarr; Back to Table of Contents](#table-of-contents)

- **YAML Configuration**: Define scraping tasks using simple and readable YAML files.
- **Flexible Selectors**: Use CSS selectors to target specific elements on web pages.
- **Interactive Scraping**: Perform clicks, form submissions, and other interactions during the scraping process.
- **Pagination Support**: Easily navigate through multiple pages of content.
- **Data Extraction**: Extract text, attributes, and custom data from web pages.
- **Variable Support**: Use variables to store and reuse data across different scraping steps.
- **Special Notations**: Use special notations to access captured data and metadata.
- **Data Transformation**: Apply custom transformations to extracted data using Python functions.
- **Multiple Output Formats**: Export scraped data in various formats, including JSON and Excel.
<!-- - **Resumable Scraping**: Ability to pause and resume scraping tasks. -->

## Installation

[&uarr; Back to Table of Contents](#table-of-contents)

1. Install Rake and its dependencies:

```zsh
pip install rake-scraper
```

2. Download the required browsers for Playwright:

```zsh
playwright install
```

These steps will install Rake, all its dependencies, and download the necessary browser binaries for web scraping.

## Usage

[&uarr; Back to Table of Contents](#table-of-contents)

### CLI

[&uarr; Back to Table of Contents](#table-of-contents)

1. Create a YAML configuration file defining your scraping task.

```yaml
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

```zsh
rakestart example.com.yaml
```

3. Rake will execute the scraping task and save the results according to your configuration.

### Programmatically

[&uarr; Back to Table of Contents](#table-of-contents)

```python
from rake import Rake

# Loads config from file into a python dict
config = Rake.load_config("example.com.yaml")

# Initialize Rake with the config
rake = Rake(config)

try:
  # start scraping
  data = await rake.start()
except Exception as e:
  ...
finally:
  # cleanup
  await rake.end()
```

## Configurations

[&uarr; Back to Table of Contents](#table-of-contents)

Rake uses various nested configuration options. These options define the structure and behavior of your scraping tasks. Here's an overview of the various configuration sections:

_**Note**: configuration will be written in YAML throughout this documentation, although Rake itself accepts Python dictionaries as configuration._

### Browser Settings `browser`

[&uarr; Back to Table of Contents](#table-of-contents)

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

```yaml
browser:
  type: firefox
  show: true
  timeout: 120000
  slowdown: 500
  ready_on: load
  block: [image, other]
```

### Logging `logging`

[&uarr; Back to Table of Contents](#table-of-contents)

The `logging` configuration option controls the verbosity of Rake's output during execution. It can be set to either `true` or `false`:

- `true`: Enables detailed logging, providing information about page openings, interactions, and other operations.
- `false`: Disables logging, resulting in minimal output (default).

**Example configuration:**

```yaml
logging: true
browser: ...
```

### Portal `portal`

[&uarr; Back to Table of Contents](#table-of-contents)

The `portal` configuration option allows you to define custom functions that can be used throughout the automation process. These functions can be used to perform various tasks such as data transformation, link generation, and more.

**Example:**

```yaml
portal: true
```

[See Portal Actions](#portal-actions)

### Output Settings `output`

[&uarr; Back to Table of Contents](#table-of-contents)

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
    - `csv`
    - `excel`
    - and any other format using portal actions
  - Format object properties:

    - `type` (string): The format type (required)
      a `:` can be used to specify the file extension, e.g. `csv:txt`, `no_extension:`

    - `transform` (string): Name of a custom python module with a `transform` function (optional)

      ```yaml
      # to_excel.py

      import pandas as pd

      def transform(data):
        ...
      ```

**Example configuration:**

```yaml
output:
  path: outputs/
  name: example.com
  formats:
    - json
    - type: excel
      transform: to_excel # no file extension needed and must not be in a nested directory
```

### Rake Pages `rake`

[&uarr; Back to Table of Contents](#table-of-contents)

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

```yaml
rake:
  - link: https://example.com
    interact: ...
```

### Interactions `interact`

[&uarr; Back to Table of Contents](#table-of-contents)

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

```yaml
interact:
  repeat: 3
  nodes:
    - selector: .pagination-item-next-page
      wait: 1000
      actions:
        - type: click
  ...
```

### Capturing and Queuing Links `links`

[&uarr; Back to Table of Contents](#table-of-contents)

The `links` configuration allows Rake to collect and queue links from the elements for further crawling. Each link configuration can include the following settings:

- `name` (string): The name to identify the collected links.
  **Example usage:**

  ```yaml
  # add links
  link:
    - name: products_page
    ...

  # then
  rake:
    - link: $products_page
    ...
  ```

- `url` (string): The URL or a JavaScript expression to evaluate and extract the link. (required)
- `smith` (string): The name of a portal action to use on the link, to manipulate or generate multiple links.
- `metadata` (object): Additional metadata to associate with the collected link. Each key-value pair can be:
  - `key` (string): The name of the metadata field.
  - `value` (string): The value or a JavaScript expression to evaluate and extract the metadata.
    **Example:**
  ```yaml
  metadata:
    category_name: '$attr{text@h1}'
    ...
  ```

**Example configuration:**

```yaml
links:
  - name: collections
    url: $attr{href@a}
    metadata:
      id: $attr{text@span.id}
```

### Extracting Data `data`

[&uarr; Back to Table of Contents](#table-of-contents)

The `data` configuration allows Rake to extract and structure data from the elements. Each data configuration can include the following settings:

- `scope` (string): The scope or path where the extracted data will be stored.
  **Example usage:**

  ```yaml
  scope: collections
  ```

  **Example with nested object:**

  ```yaml
  # product is an object
  scope: product.variant

  # find collection by name
  scope: collections.$key{name=$collection_name}.products
  ```

  **Example with nested object:**

- `value` (string | list | object): The value to extract. It can be a string, a list of strings, or an object with key-value pairs where each value is a string or an object.
  **Example usage:**

  ```yaml
  value: $attr{text@h1}
  ```

  **Example with list:**

  ```yaml
  value:
    - $attr{text@h1}
    - $attr{href@a}
  ```

  **Example with object:**

  ```yaml
  value:
    name: $attr{text@h1}
    url: $attr{href@a}
  ```

**Example configuration:**

### Concurrency `race`

[&uarr; Back to Table of Contents](#table-of-contents)

The `race` configuration option controls how many links Rake will scrape concurrently.

- `number` (integer): The number of links to scrape concurrently.
- Default value: 1 (scrape pages sequentially)

**Example:**

```yaml
race: 5 # scrape 5 links concurrently
```

## Data Transformation

[&uarr; Back to Table of Contents](#table-of-contents)

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

```python
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

```yaml
output:
  ...
  formats:
    - type: excel
      transform: to_excel
```

## Portal Actions

[&uarr; Back to Table of Contents](#table-of-contents)

Portal actions are a way to extend and provide custom functions for use in various stages in the automation e.g. Custom file output and processing captured links etc.

### Setup using `portal.py`

[&uarr; Back to Table of Contents](#table-of-contents)

Create a `portal.py` file in the root of your working directory.

**Example:**

```python
# portal.py

def to_html(data, filepath):
  ...

def generate_pagination_links(url, link_name):
  ...

def remove_currency(value):
...
```

Then set the `portal` option in your configuration to `true`. Now you can use the functions in your configuration, by providing the function name and arguments where applicable.

**Example:**

```yaml
portal: true # enable portal actions
output:
  name: example.com
  path: outputs
  formats:
    - type: html
      transform: to_html # the name of the function to use
```

### Setup using `dict`

[&uarr; Back to Table of Contents](#table-of-contents)

You can also setup portal actions using a `dict` in your configuration, by passing a dictionary of functions to the `portal` option.

**Example:**

```python
from rake import Rake

def to_html(data, filepath):
  ...

def generate_pagination_links(url, link_name):
  ...

def remove_currency(value):
  ...

rake = Rake({
  'portal': {
    'to_html': to_html,
    'generate_pagination_links': generate_pagination_links
  },
  'output': {
    'name': 'example.com',
    'path': 'outputs',
    'formats': [
      {
        'type': 'html',
        'transform': 'to_html'
      }
    ]
  }
})
```

### Portal Usage

[&uarr; Back to Table of Contents](#table-of-contents)

Portal actions can be used in the:

- Output formats `transform` option

  **Example:**

  ```yaml
  output:
    ...
    formats:
      - type: html
        transform: to_html
  ```

- Link `smith` option

  **Example:**

  ```yaml
  links:
    - name: pagination_links
      url: $attr{href}
      smith: generate_pagination_links
  ```

- `$attr{...}` utility function

  **Example:**

  ```yaml
  data:
    - scope: product
      value: $attr{text@.price | remove_currency}
  ```

## Output Formats

[&uarr; Back to Table of Contents](#table-of-contents)

Rake currently supports the following output formats:

- `json`
- `yaml`
- `csv`
- `excel`
- Using portal actions, you can output any file format you want.

## Special Notations

[&uarr; Back to Table of Contents](#table-of-contents)

Rake uses special notations to access and captured data and metadata. These notations provide a simplified way to extract and manipulate data during the scraping process.

### DOM Element Access

[&uarr; Back to Table of Contents](#table-of-contents)

Full notation:

`$attr{attribute:child(n)<page|parent.all|first>@selector | util arg | another_util >> set_var}`

Lets break it down:

1. `$attr{...}`: This is the main wrapper for the attribute extraction syntax.

2. `attribute`: Specifies the attribute to extract from the selected element(s). Common attributes include:

   - `text`: The text content of the element
   - `href`: The URL in an anchor tag
   - `src`: The source URL in an image or script tag
   - Any other HTML attribute name (e.g., `class`, `id`, `data-*`)

3. `:child(n)` (optional): Selects the nth child node of the matched element(s). can be especially useful when selecting precise TextNode

   - Example: `:child(2)` selects the second child

4. `<page|parent.all|first>` (optional): Specifies the scope of the selection:

   - `page`: Selects from the entire page
   - `parent`: Selects from the parent element (useful in nested selections)
   - `.all`: Selects all matching elements instead of just the first one
   - `.first`: Selects only the first matching element (default behavior if not specified)

5. `@selector` (optional): The CSS selector used to find the element(s) on the page.

   - Example: `@div.product-title` selects elements with class "product-title"

6. `| util arg | another_util arg` (optional): Applies a list of utility functions separated by `|` to the extracted value:

   - `util`: The name of the utility function
   - `arg`: Optional argument(s) for the utility function
   - Example: `| subtract 1` subtracts 1 from the extracted value

7. `>> set_var` (optional): Stores the result in a variable for later use:
   - `set_var`: The name of the variable to store the result

Here's an example of how this notation might be used in practice:

```yaml
data:
  - scope: product
    value: $attr{text:child(2)<parent.all>@div.product-info | trim >> product_name}
```

This would:

1. Select all `div` elements with class `product-info` within the parent context
2. For each of these elements, get the text content of their second child
3. Trim any whitespace from the extracted text
4. Store the result in a variable called `product_name`

This is a notation that aims to condense an simplify describing DOM nodes access for precise data extraction and manipulation, making it possible to handle complex scraping scenarios with a single, concise expression.

### Variable Access

[&uarr; Back to Table of Contents](#table-of-contents)

- `$var{variable_name}`: Accesses a previously stored variable.
  - Example: `$var{product_title}` retrieves the value stored in the "product_title" variable.

### Combining Notations

[&uarr; Back to Table of Contents](#table-of-contents)

Rake allows you to combine the `$attr{...}` and `$var{...}` notations to create dynamic string values, which can be particularly useful for constructing URLs.

#### Syntax

The general syntax for combining these notations is:

```
"{$attr{...}}{$var{...}}"
```

You can include as many `$attr{...}` and `$var{...}` expressions as needed within the string, along with any static text.

#### Examples

1. Constructing a URL:

```yaml
links:
  - name: product_pages
    url: 'https://example.com/products/{$attr{text@.product-id}}'
```

This would construct a URL by combining a static base URL with a product ID extracted from the page.

2. Creating a dynamic file path:

```yaml
data:
  - scope: product
    value:
      image_url: '/images/{$var{category}}/{$attr{src@img.product-image}}'
```

This would create an image URL path by combining a variable `category` with an image source attribute extracted from the page.

3. Forming a complex string:

```yaml
data:
  - scope: product
    value:
      full_name: '{$attr{text@.first-name}} {$attr{text@.last-name}} - {$var{company}}'
```

This would create a full name string by combining first name and last name attributes with a company variable.

#### Best Practices

1. Ensure that the `$attr{...}` expressions are valid and target existing elements on the page.
2. Make sure that any `$var{...}` references point to previously set variables.
3. Use this combination technique judiciously to keep your configurations readable and maintainable.
4. Ensure that the `$attr{...}` and `$var{...}` expressions yield a string value.

### Links Name Reference

[&uarr; Back to Table of Contents](#table-of-contents)
Rake allows you to capture and reference groups of links for later crawling. This feature is particularly useful for scraping multiple similar pages e.g the product page.

#### Capturing Links

To capture a group of links, use the `name` property within the `links` configuration of a node config:

```yaml
rake:
  - link: https://example.com/category-1
    interact:
      nodes:
        - selector: a.product-page
          all: true
          links:
            - name: product_pages
              url: $attr{href}
```

In this example, all links matching the `a.product-page` selector will be captured and stored under the name "product_pages".

#### Referencing Captured Links

To reference the captured links in subsequent scraping tasks, use the `$` prefix followed by the link group name in the `link` property of a rake configuration:

```yaml
rake:
  - link: $product_pages
    interact:
      nodes:
        - selector: .product
          data:
            - scope: products
              value:
                title: $attr{text@h2}
                price: $attr{text@.price}
```

This configuration will iterate through all the links captured in the "product_pages" group and perform the specified interactions and data extraction on each page.

#### Multiple Link Groups

You can capture and reference multiple link groups in your configuration:

```yaml
rake:
  - link: https://example.com/categories
    interact:
      nodes:
        - selector: .category-link
          links:
            - name: category_pages
              url: $attr{href}
  - link: $category_pages
    interact:
      nodes:
        - selector: .product-link
          links:
            - name: product_pages
              url: $attr{href}
  - link: $product_pages
    interact:
      nodes:
        - selector: .product-details
          data:
            - scope: products
              value:
                title: $attr{text@h1}
                description: $attr{text@.description}
                price: $attr{text@.price}
```

This configuration demonstrates a three-level crawl:

1. Capture category links from the main page
2. Visit each category page and capture product links
3. Visit each product page and extract detailed information

By using link group naming and referencing, you can create complex, multi-level scraping tasks that navigate through website structures efficiently.

### Data Scoping: Forming the structure of the data

[&uarr; Back to Table of Contents](#table-of-contents)

Data scoping allows you to navigate and build flexible data with complex nested structures. This feature is available in the `rake.*.interact.*.data.*.scope` configuration.

#### Scoping Notation

The general format for data scoping is:

`object.$key{left_operand operator right_operand}.property`

Let's break down each component:

1. `object`: The base object or collection you're working with.
2. `$key{...}`: A special syntax for finding a specific item within a collection.
3. `property`: The specific property of the found item you want to access / updated.

#### Key Matching Syntax

The `$key{...}` syntax is particularly useful for finding items in collections. It uses the following format:

`$key{left_operand operator right_operand}`

Where:

- `left_operand`: The property of the items to compare (can be a variable with `$` prefix).
- `operator`: One of `=`, `!=`, `>=`, `<=`, `>`, `<`.
- `right_operand`: The value to compare against (can be a variable with `$` prefix).

#### How It Works

1. The system searches through the `object` (which can be a dict or list).
2. For each item, it compares the `left_operand` property with the `right_operand` using the specified `operator`.
3. If a match is found, that item is selected.
4. The `property` after the `$key{...}` is then accessed on the matched item.

#### Supported Operators

- `=`: Equality
- `!=`: Inequality
- `>=`: Greater than or equal to
- `<=`: Less than or equal to
- `>`: Greater than
- `<`: Less than

#### Variable Usage

You can use variables in both the `left_operand` and `right_operand` by prefixing them with `$`. The actual values will be looked up in the `vars` or link `metadata` dictionary.

#### Examples

1. Basic usage:

   ```
   users.$key{name=John}.hobbies
   ```

   This would find a user with the name "John" and add data under `hobbies` key.

2. Using variables:

   ```
   products.$key{$category=electronics}.variants
   ```

   This would find a product in the "electronics" category (where `category` is a variable) and add data under `variants` key.

3. Numeric comparison:
   ```
   orders.$key{total>100}.items
   ```
   This would find an order with a total greater than 100 and add data under `items` key.

#### Best Practices

1. Ensure that the properties you're comparing exist in your data structure.
2. Be mindful of the data types when using comparison operators.
3. Use variables (`$var`) when you need dynamic comparisons.
<!-- 4. Handle potential errors (like no match found) in your Rake tasks. -->

By mastering data scoping, you can efficiently navigate and extract data from complex structures in your Rake configurations, making your tasks more powerful and flexible.

## License

[&uarr; Back to Table of Contents](#table-of-contents)

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
