<template>
  <div class="hello">
    <h1>{{ msg }}</h1>
  </div>
  <canvas id="myChart" width="400" height="400"></canvas>
</template>

<script>
import Chart from "chart.js/auto";
export default {
  name: "HelloWorld",
  props: {
    msg: String,
  },
  mounted() {
    console.log("component mounted");

    const ctx = document.getElementById("myChart");
    const myChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: [1, 2, 3, 4],
        datasets: [
          {
            label: "Temperature (F)",
            data: [77, 78, 80, 86],
            // showLine: true,
            borderColor: "red",
          },
          {
            label: "Relative Humidity",
            data: [66, 68, 69, 77],
            borderColor: "blue",
          },
        ],
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
