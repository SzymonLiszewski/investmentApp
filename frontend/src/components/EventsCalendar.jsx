import React, { useEffect, useState } from 'react';
import { Calendar, momentLocalizer } from 'react-big-calendar';
import moment from 'moment';
import Modal from 'react-modal';
import 'react-big-calendar/lib/css/react-big-calendar.css';
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
    <div>
      <h1 style={{textAlign: 'center', marginTop: '50px'}}>Financial Events Calendar</h1>
      <Calendar
        localizer={localizer}
        events={events}
        startAccessor="ipoDate"
        endAccessor="endDate"
        style={{ height: '75vh',
           marginLeft: '5vw',
           marginRight: '5vw',
           width: '90vw',
          color: 'black'  }}
        onSelectEvent={handleEventClick}
      />
      {selectedEvent && (
        <Modal
          isOpen={!!selectedEvent}
          onRequestClose={closeModal}
          contentLabel="Event Details"
        >
          <h2 style={{color: 'black'}}>{selectedEvent.title}</h2>
          <p style={{color: 'black'}}>
            Start: {selectedEvent.ipoDate.toLocaleString()}
          </p>
          <p style={{color: 'black'}}>
            End: {selectedEvent.endDate.toLocaleString()}
          </p>
          <button onClick={closeModal}>Close</button>
        </Modal>
      )}
    </div>
  );
};

export default EventsCalendar;
