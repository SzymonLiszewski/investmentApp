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
  // Semicircle gauge: the arc only occupies the top half of the pie, so use a
  // 200x120 canvas with the pie centre anchored near the bottom edge — this keeps
  // the rendered box the same size as the visible arc (no invisible empty half).
  const chartWidth = 200;
  const chartHeight = 120;
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
        <PieChart width={chartWidth} height={chartHeight}>
          <Pie
            data={gaugeData}
            startAngle={180}
            endAngle={0}
            cy={100}
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