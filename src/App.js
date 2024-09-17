import React, { useState, useEffect } from "react";
import { Line } from "react-chartjs-2";
import io from "socket.io-client";
import 'chartjs-adapter-date-fns'; // Importa el adaptador de fechas
import { Chart, registerables } from "chart.js";
import GaugeChart from 'react-gauge-chart';
import './App.css';

Chart.register(...registerables);

const socket = io("http://localhost:5000", {
  transports: ['websocket', 'polling'],  // Opciones de transporte
});

function App() {

  const [data, setData] = useState({
    labels: [],
    datasets: [
      {
        label: "Temperatura",
        data: [],
        backgroundColor: "rgba(255, 99, 132, 0.2)",
        borderColor: "rgba(255, 99, 132, 1)",
        borderWidth: 1,
      },
    ],
  });

  const [latestReading, setLatestReading] = useState({ timestamp: null, value: null });

  const [readings, setReadings] = useState([]);

  useEffect(() => {
    socket.on("new_data", (data) => {
      console.log("Data received:", data);

      if (data.length > 0) {
        const latest = data[data.length - 1]; // Obtener la última lectura
        setLatestReading({ timestamp: new Date(latest.__timestamp), value: latest.__value });
        setReadings((prevReadings) => [...prevReadings, ...data]);

        const newData = {
          labels: data.map((item) => new Date(item.__timestamp)),
          datasets: [
            {
              label: "Temperatura",
              data: data.map((item) => ({ x: new Date(item.__timestamp), y: item.__value })),
              backgroundColor: "rgba(255, 99, 132, 0.2)",
              borderColor: "rgba(255, 99, 132, 1)",
              borderWidth: 1,
            },
          ],
        };
        setData(newData);
      }

    });

    return () => socket.off("new_data");
  }, []);


  return (
    <div>

      <div className="chart-container">
        <Line
          data={data}
          options={{
            responsive: true,
            scales: {
              x: {
                type: 'time',
                time: {
                  unit: 'second',
                  stepSize: 1,
                  //tooltipFormat: 'll HH:mm:ss',
                },
                ticks: {
                  autoSkip: true,
                  maxTicksLimit: 10,
                },
              },
              y: {
                beginAtZero: true,
              },
            },
            animation: {
              duration: 0, // Desactiva la animación para actualizaciones en tiempo real
            },
          }}
        />

        
        
      </div>
      
      <div className="gauge-container">
          {/* Muestra solo la última lectura */}
          {latestReading.timestamp && (
            <div>
              <p>{latestReading.timestamp.toLocaleString()}</p>
              <p>Temperatura: {latestReading.value}</p>
            </div>
          )}

          {/* Gráfico Gauge */}
          {readings.length > 0 && (
            <GaugeChart
              id="gauge-chart"
              nrOfLevels={1} // Más niveles para un gráfico más detallado
              colors={["#28a745"]}
              arcWidth={0.5} // Ajustar el grosor del arco
              percent={readings[readings.length - 1].__value / 100} // Ajustar porcentaje según el valor
              needleColor="#34568B" // Color de la aguja
              needleBaseColor="#888888" // Color de la base de la aguja
              textColor="#000000" // Color del texto
            />
          )}
      </div>
    

    </div>
  );
}
  
export default App;
