import React, { useState } from 'react';
import { Calendar, momentLocalizer } from 'react-big-calendar';
import moment from 'moment';
import Modal from 'react-modal';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import 'moment/locale/en-gb';

moment.locale('en-gb');
const localizer = momentLocalizer(moment);

Modal.setAppElement('#root'); // Set the app root for accessibility

const EventsCalendar = () => {
  const [events, setEvents] = useState([
    {
      title: 'Apple Q2 Earnings',
      start: new Date(2024, 7, 1, 10, 0),
      end: new Date(2024, 7, 1, 12, 0),
      allDay: false,
    },
    {
      title: 'Google Dividend Payout',
      start: new Date(2024, 7, 2, 14, 0),
      end: new Date(2024, 7, 2, 15, 0),
      allDay: false,
    },
    // Dodaj więcej wydarzeń
  ]);

  const [selectedEvent, setSelectedEvent] = useState(null);

  const handleEventClick = event => {
    setSelectedEvent(event);
  };

  const closeModal = () => {
    setSelectedEvent(null);
  };

  return (
    <div>
      <h1>Financial Events Calendar</h1>
      <Calendar
        localizer={localizer}
        events={events}
        startAccessor="start"
        endAccessor="end"
        style={{ height: 500, margin: '50px' }}
        onSelectEvent={handleEventClick}
      />
      {selectedEvent && (
        <Modal
          isOpen={!!selectedEvent}
          onRequestClose={closeModal}
          contentLabel="Event Details"
        >
          <h2>{selectedEvent.title}</h2>
          <p>
            St    art: {selectedEvent.start.toLocaleString()}
          </p>
          <p>
            End: {selectedEvent.end.toLocaleString()}
          </p>
          <button onClick={closeModal}>Close</button>
        </Modal>
      )}
    </div>
  );
};

export default EventsCalendar;
