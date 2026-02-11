import React from 'react';
import { PieChart, Pie, Cell, Tooltip, Label } from 'recharts';

const IndicatorsGaugeChart = ({ data, range, name, interpretation }) => {
  const value = Math.min(Math.max(data, range[0]), range[1]);
  const rangeSpan = range[1] - range[0];
  const filledDegrees = rangeSpan === 0 ? 0 : ((value - range[0]) / rangeSpan) * 180;
  const gaugeData = [
    { name, value: filledDegrees, fill: '#8884d8' },
    { name: 'Remaining', value: 180 - filledDegrees, fill: '#e0e0e0' },
  ];
  const chartSize = 200;
  const displayValue = Number.isFinite(data) ? data.toFixed(2) : '—';
  if (data == null || data === -100) {
    return (
      <div className="indicatorGauge">
        <div className="indicatorChartWrap">
          <div className="indicatorGaugePlaceholder">—</div>
        </div>
        <div className="indicatorTextBlock">
          <span className="indicatorName">{name}</span>
          <p className="indicatorInterpretation">No data</p>
        </div>
      </div>
    );
  }

  return (
    <div className="indicatorGauge">
      <div className="indicatorChartWrap">
        <PieChart width={chartSize} height={chartSize}>
          <Pie
            data={gaugeData}
            startAngle={180}
            endAngle={0}
            innerRadius={60}
            outerRadius={80}
            dataKey="value"
          >
            {gaugeData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.fill} />
            ))}
            <Label
              value={displayValue}
              position="center"
              fill="#000"
              fontSize="24px"
              fontWeight="bold"
            />
          </Pie>
          <Tooltip />
        </PieChart>
      </div>
      <div className="indicatorTextBlock">
        <span className="indicatorName">{name}</span>
        <p className="indicatorInterpretation">{interpretation}</p>
      </div>
    </div>
  );
};

export default IndicatorsGaugeChart;