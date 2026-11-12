# Operational Verification Labs: 03 Interactive Dashboards With D3 And Plotly

## Objective & Environment Setup

The objective of this lab is to build, deploy, and verify interactive dashboards using D3.js and Plotly.js. These tools are essential for creating dynamic and interactive data visualizations that can be embedded in web applications. The lab will guide you through the process of implementing a dashboard, tuning its performance, and ensuring it handles edge cases gracefully.

### Environment Setup

Ensure you have the following environment and tools installed:

- **Python 3.11+**: Required for running the Python scripts.
- **Node.js**: Required for serving the web application.
- **npm**: Node package manager for installing D3.js and Plotly.js.
- **Jupyter Notebook**: Optional, for interactive development and visualization.
- **Pandas**: For data manipulation and analysis.
- **Flask**: For serving the web application.
- **Requests**: For making HTTP requests to APIs.

You can install the required Python packages using pip:

```bash
pip install pandas flask requests
```

For Node.js and npm, you can download and install them from the [official Node.js website](https://nodejs.org/).

## Exercise 1: Hands-On Implementation & Pipeline Execution

In this exercise, we will create a simple interactive dashboard using both D3.js and Plotly.js. We will use a dataset from a public API to demonstrate the capabilities of these libraries.

### Step 1: Fetch Data from an API

First, we will fetch data from a public API using Python. For this example, we will use the [JSONPlaceholder API](https://jsonplaceholder.typicode.com/).

```python
import requests
import pandas as pd

def fetch_data():
    response = requests.get("https://jsonplaceholder.typicode.com/posts")
    data = response.json()
    df = pd.DataFrame(data)
    return df

data = fetch_data()
print(data.head())
```

### Step 2: Serve Data via Flask

Next, we will create a simple Flask application to serve the data to our web application.

```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/data', methods=['GET'])
def get_data():
    return jsonify(data.to_dict(orient='records'))

if __name__ == '__main__':
    app.run(debug=True)
```

### Step 3: Create the Web Application with D3.js

Create an HTML file named `d3_dashboard.html` and include the D3.js library.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>D3.js Dashboard</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
</head>
<body>
    <h1>D3.js Dashboard</h1>
    <div id="chart"></div>
    <script>
        d3.json('/data').then(data => {
            const svg = d3.select("#chart")
                .append("svg")
                .attr("width", 800)
                .attr("height", 600);

            const xScale = d3.scaleBand()
                .domain(data.map(d => d.userId))
                .range([0, 800])
                .padding(0.1);

            const yScale = d3.scaleLinear()
                .domain([0, d3.max(data, d => d.id)])
                .nice()
                .range([600, 0]);

            svg.selectAll("rect")
                .data(data)
                .enter()
                .append("rect")
                .attr("x", d => xScale(d.userId))
                .attr("y", d => yScale(d.id))
                .attr("width", xScale.bandwidth())
                .attr("height", d => 600 - yScale(d.id))
                .attr("fill", "steelblue");
        });
    </script>
</body>
</html>
```

### Step 4: Create the Web Application with Plotly.js

Create another HTML file named `plotly_dashboard.html` and include the Plotly.js library.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Plotly.js Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <h1>Plotly.js Dashboard</h1>
    <div id="chart"></div>
    <script>
        fetch('/data')
            .then(response => response.json())
            .then(data => {
                const userIds = data.map(d => d.userId);
                const ids = data.map(d => d.id);

                const trace = {
                    x: userIds,
                    y: ids,
                    type: 'bar',
                    marker: { color: 'steelblue' }
                };

                const layout = {
                    title: 'Posts by User',
                    xaxis: { title: 'User ID' },
                    yaxis: { title: 'Post ID' }
                };

                Plotly.newPlot('chart', [trace], layout);
            });
    </script>
</body>
</html>
```

### Step 5: Run the Flask Application

Run the Flask application to serve the data and the web applications.

```bash
python app.py
```

Open your browser and navigate to `http://127.0.0.1:5000/d3_dashboard.html` and `http://127.0.0.1:5000/plotly_dashboard.html` to see the dashboards.

## Exercise 2: Hyperparameter Tuning & Empirical Benchmarking

In this exercise, we will benchmark the performance of the dashboards by measuring the time taken to render the charts.

### Step 1: Measure Render Time with D3.js

Add a timer to measure the render time of the D3.js chart.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>D3.js Dashboard</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
</head>
<body>
    <h1>D3.js Dashboard</h1>
    <div id="chart"></div>
    <script>
        const startTime = performance.now();

        d3.json('/data').then(data => {
            const svg = d3.select("#chart")
                .append("svg")
                .attr("width", 800)
                .attr("height", 600);

            const xScale = d3.scaleBand()
                .domain(data.map(d => d.userId))
                .range([0, 800])
                .padding(0.1);

            const yScale = d3.scaleLinear()
                .domain([0, d3.max(data, d => d.id)])
                .nice()
                .range([600, 0]);

            svg.selectAll("rect")
                .data(data)
                .enter()
                .append("rect")
                .attr("x", d => xScale(d.userId))
                .attr("y", d => yScale(d.id))
                .attr("width", xScale.bandwidth())
                .attr("height", d => 600 - yScale(d.id))
                .attr("fill", "steelblue");

            const endTime = performance.now();
            console.log(`D3.js render time: ${endTime - startTime} milliseconds`);
        });
    </script>
</body>
</html>
```

### Step 2: Measure Render Time with Plotly.js

Add a timer to measure the render time of the Plotly.js chart.

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Plotly.js Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <h1>Plotly.js Dashboard</h1>
    <div id="chart"></div>
    <script>
        const startTime = performance.now();

        fetch('/data')
            .then(response => response.json())
            .then(data => {
                const userIds = data.map(d => d.userId);
                const ids = data.map(d => d.id);

                const trace = {
                    x: userIds,
                    y: ids,
                    type: 'bar',
                    marker: { color: 'steelblue' }
                };

                const layout = {
                    title: 'Posts by User',
                    xaxis: { title: 'User ID' },
                    yaxis: { title: 'Post ID' }
                };

                Plotly.newPlot('chart', [trace], layout);

                const endTime = performance.now();
                console.log(`Plotly.js render time: ${endTime - startTime} milliseconds`);
            });
    </script>
</body>
</html>
```

### Step 3: Compare Render Times

Open the browser's developer console to compare the render times of the D3.js and Plotly.js charts.

## Exercise 3: Stress Testing, Edge Cases & Failure Mitigation

In this exercise, we will test the dashboards for edge cases and implement guardrails to handle potential failures.

### Step 1: Test with Large Data

Modify the Flask application to serve a larger dataset.

```python
def fetch_large_data():
    response = requests.get("https://jsonplaceholder.typicode.com/posts")
    data = response.json() * 100  # Repeat the data 100 times
    df = pd.DataFrame(data)
    return df

data = fetch_large_data()
print(data.head())
```

### Step 2: Implement Error Handling

Add error handling to the D3.js and Plotly.js charts to handle potential data fetching errors.

#### D3.js Error Handling

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>D3.js Dashboard</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
</head>
<body>
    <h1>D3.js Dashboard</h1>
    <div id="chart"></div>
    <script>
        d3.json('/data')
            .then(data => {
                const svg = d3.select("#chart")
                    .append("svg")
                    .attr("width", 800)
                    .attr("height", 600);

                const xScale = d3.scaleBand()
                    .domain(data.map(d => d.userId))
                    .range([0, 800])
                    .padding(0.1);

                const yScale = d3.scaleLinear()
                    .domain([0, d3.max(data, d => d.id)])
                    .nice()
                    .range([600, 0]);

                svg.selectAll("rect")
                    .data(data)
                    .enter()
                    .append("rect")
                    .attr("x", d => xScale(d.userId))
                    .attr("y", d => yScale(d.id))
                    .attr("width", xScale.bandwidth())
                    .attr("height", d => 600 - yScale(d.id))
                    .attr("fill", "steelblue");
            })
            .catch(error => {
                console.error("Error fetching data:", error);
                d3.select("#chart").append("p").text("Failed to load data.");
            });
    </script>
</body>
</html>
```

#### Plotly.js Error Handling

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Plotly.js Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <h1>Plotly.js Dashboard</h1>
    <div id="chart"></div>
    <script>
        fetch('/data')
            .then(response => response.json())
            .then(data => {
                const userIds = data.map(d => d.userId);
                const ids = data.map(d => d.id);

                const trace = {
                    x: userIds,
                    y: ids,
                    type: 'bar',
                    marker: { color: 'steelblue' }
                };

                const layout = {
                    title: 'Posts by User',
                    xaxis: { title: 'User ID' },
                    yaxis: { title: 'Post ID' }
                };

                Plotly.newPlot('chart', [trace], layout);
            })
            .catch(error => {
                console.error("Error fetching data:", error);
                document.getElementById('chart').innerHTML = "<p>Failed to load data.</p>";
            });
    </script>
</body>
</html>
```

### Step 3: Test Edge Cases

Test the dashboards with different edge cases, such as empty data, missing fields, and invalid data types.

## Verification Checklist & Quick Reference Cheat Sheet

### Essential Python Methods and Parameters

- `requests.get(url)`: Fetch data from a URL.
- `pandas.DataFrame(data)`: Create a DataFrame from data.
- `jsonify(data)`: Convert data to JSON format.
- `fetch(url)`: Fetch data from a URL in JavaScript.
- `d3.json(url)`: Fetch JSON data in D3.js.
- `Plotly.newPlot(id, data, layout)`: Create a Plotly chart.

### Verification Flags

- `debug=True`: Enable debug mode in Flask.
- `performance.now()`: Measure performance in JavaScript.

### CLI Commands

- `pip install pandas flask requests`: Install required Python packages.
- `node -v`: Check Node.js version.
- `npm -v`: Check npm version.
- `python app.py`: Run the Flask application.

By following this lab guide, you will have a solid understanding of how to create, deploy, and verify interactive dashboards using D3.js and Plotly.js.
