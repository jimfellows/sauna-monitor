<template>
  <div class="hello">
    <h1>{{ msg }}</h1>
  </div>
  <canvas id="myChart" width="400" height="400"></canvas>
</template>

<script>
import Chart from "chart.js/auto";
export default {
  name: "LineChart",
  props: {
    msg: String,
  },
  mounted() {
    console.log("component mounted");
    // const PouchDB = require("pouchdb");

    // const PouchDB = require("pouchdb-browser");
    const PouchDB = require("pouchdb").default;
    const sensorData = new PouchDB(
      "http://admin:admin@192.168.1.101:5984/home-sensors"
    );
    const temps = [];
    const hums = [];
    const xaxis = [];
    const getData = function () {
      console.info("Getting data");
      sensorData.query("basicQueries/todaysSaunaReadings").then(function (doc) {
        for (const r of doc.rows) {
          temps.push(r.value.tempF);
          hums.push(r.value.humidity);
          xaxis.push(r.value.dt);
        }
      });
    };
    getData();
    Promise.resolve(temps);
    Promise.resolve(hums);
    Promise.resolve(xaxis);
    console.info(hums);
    // console.info(data);
    const ctx = document.getElementById("myChart");
    const myChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: xaxis,
        datasets: [
          {
            label: "Temperature (F)",
            data: temps,
            yAxisId: "tempY",
            borderColor: "red",
          },
          {
            label: "Relative Humidity",
            data: hums,
            yAxisId: "humY",
            borderColor: "blue",
          },
        ],
      },
      options: {
        scales: {
          y1: {
            stacked: false,
            position: "left",
            type: "linear",
            scaleLabel: {
              display: true,
            },
            id: "tempY",
          },
          y2: {
            stacked: false,
            position: "right",
            type: "linear",
            id: "humY",
          },
        },
      },
    });

    myChart;
  },
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
h3 {
  margin: 40px 0 0;
}
ul {
  list-style-type: none;
  padding: 0;
}
li {
  display: inline-block;
  margin: 0 10px;
}
a {
  color: #42b983;
}
</style>
