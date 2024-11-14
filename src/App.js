import React, { useState, useEffect } from "react";
import { Line } from "react-chartjs-2";
import GaugeChart from 'react-gauge-chart';
import io from "socket.io-client";
import 'chartjs-adapter-date-fns';
import { Chart, registerables } from "chart.js";
import './App.css';

Chart.register(...registerables);

const socket = io("http://192.168.0.39:5000", {
  transports: ['websocket', 'polling']
});

const metrics = ["temperature", "humidity", "pressure"];

function App() {
  const [chartData, setChartData] = useState({
    temperature: { labels: [], datasets: [{ label: "Temperature", data: [] }] },
    humidity: { labels: [], datasets: [{ label: "Humidity", data: [] }] },
    pressure: { labels: [], datasets: [{ label: "Pressure", data: [] }] }
  });
  
  const [latestReadings, setLatestReadings] = useState({
    temperature: null,
    humidity: null,
    pressure: null
  });

  useEffect(() => {
    socket.on("new_data", (data) => {
      metrics.forEach(metric => {
        if (data[metric]) {
          const latest = data[metric][data[metric].length - 1];
          setLatestReadings((prevReadings) => ({
            ...prevReadings,
            [metric]: latest ? { timestamp: new Date(latest.__timestamp), value: latest.__value } : null
          }));

          setChartData((prevData) => ({
            ...prevData,
            [metric]: {
              labels: data[metric].map((item) => new Date(item.__timestamp)),
              datasets: [
                {
                  label: metric.charAt(0).toUpperCase() + metric.slice(1),
                  data: data[metric].map((item) => ({ x: new Date(item.__timestamp), y: item.__value })),
                  backgroundColor: "rgba(0, 123, 255, 0.2)",
                  borderColor: "rgba(0, 123, 255, 1)",
                  borderWidth: 1,
                },
              ],
            }
          }));
        }
      });
    });

    return () => socket.off("new_data");
  }, []);

  return (
    <div>
      <div className="overview-boxes">
        {metrics.map(metric => (
          <div key={metric} className="box">
            <div className="number" id={metric}>
              {latestReadings[metric]?.value || "No data"}
            </div>
          </div>
        ))}
      </div>
      
      <div className="graph-box">
        <div className="history-charts">
          {metrics.map(metric => (
            <div key={metric} id={`${metric}-history`} className="history-divs">
              <Line data={chartData[metric]} options={{ responsive: true, scales: { x: { type: 'time', } }, }} />
            </div>
          ))}
        </div>
      </div>

      <div className="gaugeCharts">
        {metrics.map(metric => (
          <div key={metric} className="gauge-box" id={`${metric}-gauge`}>
            <GaugeChart id={`${metric}-gauge-chart`} nrOfLevels={20} percent={(latestReadings[metric]?.value || 0) / 100} />
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
