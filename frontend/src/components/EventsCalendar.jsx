import React, { useEffect, useState } from 'react';
import { Calendar, momentLocalizer } from 'react-big-calendar';
import moment from 'moment';
import Modal from 'react-modal';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import './styles/EventsCalendar.css'; // loaded AFTER the library CSS so our overrides win
import 'moment/locale/en-gb';

moment.locale('en-gb');
const localizer = momentLocalizer(moment);

Modal.setAppElement('#root'); // Set the app root for accessibility

const addHours = (date, hours) => {
  const newDate = new Date(date);
  newDate.setHours(newDate.getHours() + hours);
  return newDate;
};

// GET a calendar endpoint and return its rows, tolerating failures so one
// empty/erroring feed doesn't blank out the whole calendar.
const fetchRows = async (url) => {
  try {
    const response = await fetch(url);
    if (!response.ok) return [];
    const data = await response.json();
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
};

const EventsCalendar = () => {
  const [events, setEvents] = useState([]);
  const [selectedEvent, setSelectedEvent] = useState(null);

  useEffect(() => {
    getData();
  }, []);

  const getData = async () => {
    // Fetch IPOs and earnings together and merge them into one event list.
    const [ipoRows, earningsRows] = await Promise.all([
      fetchRows('/api/calendar/ipo/'),
      fetchRows('/api/calendar/earnings/'),
    ]);

    // IPO rows: [symbol, name, ipoDate, priceRangeLow, priceRangeHigh, currency, exchange]
    const ipoEvents = ipoRows.map((item) => {
      const start = new Date(item[2]);
      return {
        type: 'ipo',
        symbol: item[0],
        name: item[1],
        title: item[1] || item[0], // company name reads best on an IPO chip
        start,
        end: addHours(start, 2),
        priceRangeLow: item[3],
        priceRangeHigh: item[4],
        currency: item[5],
        exchange: item[6],
        allDay: false,
      };
    });

    // Earnings rows: [symbol, name, reportDate, fiscalDateEnding, estimate, currency]
    const earningsEvents = earningsRows.map((item) => {
      const start = new Date(item[2]);
      return {
        type: 'earnings',
        symbol: item[0],
        name: item[1],
        title: `${item[0]} earnings`,
        start,
        end: addHours(start, 2),
        estimate: item[4],
        currency: item[5],
        allDay: false,
      };
    });

    setEvents([...ipoEvents, ...earningsEvents]);
  };

  const handleEventClick = (event) => setSelectedEvent(event);
  const closeModal = () => setSelectedEvent(null);

  // Color-code chips so IPOs and earnings are visually distinct (see CSS).
  const eventPropGetter = (event) => ({
    className: event.type === 'earnings' ? 'rbc-event--earnings' : 'rbc-event--ipo',
  });

  return (
    // central, max-width container (styling in styles/EventsCalendar.css)
    <div className="calendarPage">
      <h1 className="calendarHeading">Financial Events Calendar</h1>
      {/* legend clarifies the two event colors */}
      <div className="calendarLegend">
        <span className="calendarLegendItem">
          <span className="calendarLegendSwatch calendarLegendSwatch--ipo" /> IPO
        </span>
        <span className="calendarLegendItem">
          <span className="calendarLegendSwatch calendarLegendSwatch--earnings" /> Earnings
        </span>
      </div>
      {/* high-contrast white card so the grid is readable on the purple background */}
      <div className="calendarCard">
        {/* wrapper enables horizontal scroll on narrow screens */}
        <div className="calendarScroll">
          <Calendar
            localizer={localizer}
            events={events}
            startAccessor="start"
            endAccessor="end"
            className="captrivioCalendar" /* height/sizing moved to CSS */
            onSelectEvent={handleEventClick}
            eventPropGetter={eventPropGetter}
          />
        </div>
      </div>
      {selectedEvent && (
        <Modal
          isOpen={!!selectedEvent}
          onRequestClose={closeModal}
          contentLabel="Event Details"
          className="eventModal"
          overlayClassName="eventModalOverlay"
        >
          <h2>{selectedEvent.title}</h2>
          {selectedEvent.type === 'ipo' && selectedEvent.name && (
            <p>{selectedEvent.name}</p>
          )}
          <p>
            {selectedEvent.type === 'ipo' ? 'IPO date' : 'Report date'}:{' '}
            {selectedEvent.start.toLocaleDateString()}
          </p>
          {selectedEvent.type === 'ipo' &&
            (selectedEvent.priceRangeLow || selectedEvent.priceRangeHigh) && (
              <p>
                Price range: {selectedEvent.priceRangeLow}–{selectedEvent.priceRangeHigh}{' '}
                {selectedEvent.currency}
              </p>
            )}
          {selectedEvent.type === 'ipo' && selectedEvent.exchange && (
            <p>Exchange: {selectedEvent.exchange}</p>
          )}
          {selectedEvent.type === 'earnings' && selectedEvent.estimate && (
            <p>EPS estimate: {selectedEvent.estimate} {selectedEvent.currency}</p>
          )}
          <button className="eventModalClose" onClick={closeModal}>Close</button>
        </Modal>
      )}
    </div>
  );
};

export default EventsCalendar;
