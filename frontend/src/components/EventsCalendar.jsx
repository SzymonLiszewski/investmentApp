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

const EventsCalendar = () => {
  const [events, setEvents] = useState([]);

const addHours = (date, hours) => {
  const newDate = new Date(date);
  newDate.setHours(newDate.getHours() + hours);
  return newDate;
};


  useEffect(()=>{
    getData()
  },[])

  let getData = async() =>{
    let response = await fetch('/api/calendar/ipo/')
    let data = await response.json()
    let transformed = await data.map(item=>({
      symbol: item[0],
      title: item[1],
      ipoDate: new Date(item[2]),
      endDate: addHours(new Date(item[2]), 2),
      priceRangeLow: item[3],
      priceRangeHigh: item[4],
      currency: item[5],
      exchange: item[6],
      allDay: false,
    }))
    setEvents(transformed)
    console.log(events)
  }

  const [selectedEvent, setSelectedEvent] = useState(null);

  const handleEventClick = event => {
    setSelectedEvent(event);
  };

  const closeModal = () => {
    setSelectedEvent(null);
  };

  return (
    // central, max-width container (styling in styles/EventsCalendar.css)
    <div className="calendarPage">
      <h1 className="calendarHeading">Financial Events Calendar</h1>
      {/* high-contrast white card so the grid is readable on the purple background */}
      <div className="calendarCard">
        {/* wrapper enables horizontal scroll on narrow screens */}
        <div className="calendarScroll">
          <Calendar
            localizer={localizer}
            events={events}
            startAccessor="ipoDate"
            endAccessor="endDate"
            className="captrivioCalendar" /* height/sizing moved to CSS */
            onSelectEvent={handleEventClick}
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
          <p>Start: {selectedEvent.ipoDate.toLocaleString()}</p>
          <p>End: {selectedEvent.endDate.toLocaleString()}</p>
          <button className="eventModalClose" onClick={closeModal}>Close</button>
        </Modal>
      )}
    </div>
  );
};

export default EventsCalendar;
