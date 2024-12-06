# GH Insights

Welcome to the GH Insights project! This project aims to provide insights and analytics for GitHub repositories.

## Table of Contents

- [Introduction](#introduction)
- [Installation](#installation)
- [Development](#usage)
- [Contributing](#contributing)
- [License](#license)

## Introduction

GH Insights is a tool designed to help developers and project managers gain valuable insights into their GitHub repositories. It provides various metrics and visualizations to help understand the health and activity of a team.

## Installation

To install GH Insights, follow these steps:

1. Clone the repository:
    ```bash
    git clone https://github.com/gsanchietti/gh-insights.git
    ```
2. Navigate to the project directory:
    ```bash
    cd gh-insights
    ```
3. [Install Hugo](https://gohugo.io/installation/), on Linux:
   ```bash
   wget https://github.com/gohugoio/hugo/releases/download/v0.139.3/hugo_extended_0.139.3_Linux-64bit.tar.gz 
   tar xvzf hugo_extended_0.139.3_Linux-64bit.tar.gz hugo
   rm -f hugo_extended_0.139.3_Linux-64bit.tar.gz
   ```
4. Setup the site:
   ```bash
   cd site
   ../hugo build
   ```


## Development

Start, Hugo dev server:
```bash
cd site
../hugo server
```

AdGenerate content:
```bash
./build.sh
```

## Contributing

We welcome contributions to GH Insights! If you would like to contribute, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Commit your changes and push them to your fork.
4. Submit a pull request with a description of your changes.

## License

This project is licensed under the GPL License. See the [LICENSE](LICENSE) file for more details.