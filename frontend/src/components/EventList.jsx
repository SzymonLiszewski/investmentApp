import React from 'react';

const EventList = ({ events, selectedDate }) => {
  const formattedDate = selectedDate.toISOString().split('T')[0]; // Formatowanie daty do porównania

  const eventsOnSelectedDate = events.filter(event => event.date === formattedDate);

  return (
    <div>
      <h2>Events on {formattedDate}</h2>
      <ul>
        {eventsOnSelectedDate.map((event, index) => (
          <li key={index}>
            <strong>{event.category}</strong>: {event.description} ({event.stock})
          </li>
        ))}
      </ul>
    </div>
  );
};

export default EventList;
