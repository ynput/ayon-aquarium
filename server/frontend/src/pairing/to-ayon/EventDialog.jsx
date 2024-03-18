import axios from "axios";
import addonData from "/src/common";

import { useRef, useState, useEffect } from "react";

import styled from "styled-components";
import { ErrorContainer, DialogTitle } from '/src/components/Styles'
import Dialog from "/src/components/Dialog";

const Table = styled.table`
  border-collapse: collapse;
  width: 100%;

  thead {
    position: sticky;
    top: 0;
    background-color: var(--md-sys-color-surface);
    border-radius: 4px;
  }

  th, td {
    padding: 0.5rem;
    height: 48px;
  }

  th {
    font-weight: bold;
    text-align: left;
  }
`

const EventDialog = ({ ayonEventId, onHide }) => {
  const intervalFn = useRef(null);
  const [ayonEvent, setAyonEvent] = useState();
  const [totalEntities, setTotalEntities] = useState(0);
  const [error, setError] = useState(null);

  function stopRefreshEvent() {
    if (intervalFn.current) clearInterval(intervalFn.current)
    intervalFn.current = null
  }

  useEffect(() => {
    stopRefreshEvent()

    intervalFn.current = setInterval(() => {
      axios
        .get(`${addonData.baseUrl}/events/${ayonEventId}`)
        .then((response) => {
          setAyonEvent(response.data)
          if (response.data.status === "finished") {
            stopRefreshEvent()
          }
        })
        .catch((error) => {
          const errorMessage = error.response.data?.traceback ||
            error.response.data?.detail ||
            "Error on server, please check server's logs";
          setError(errorMessage);
        })
    }, 1000)
  }, [ayonEventId]);

  useEffect(() => {
    let total = 0
    if (ayonEvent?.summary) {
      total = Object.values(ayonEvent.summary).reduce((total, entity) => total + entity.count, 0)
    }
    setTotalEntities(total);
  }, [ayonEvent]);

  function close() {
    stopRefreshEvent()
    onHide();
  }

  return (
    <Dialog visible={true} onHide={close}>
      {ayonEvent == null && !error && "Loading event..."}
      {ayonEvent != null &&
        <>
          <DialogTitle>
            <img height="100px" src="/ayon.png"></img>
            <h2>Syncing to Ayon <strong>{ayonEvent.project_name}</strong> project</h2>
            <h2>Sync <strong>{ayonEvent.status}</strong> for {totalEntities} entities.</h2>
          </DialogTitle>
          <Table>
            <thead>
              <tr>
                <th>Entity type</th>
                <th>Progression</th>
              </tr>
            </thead>
            <tbody>
              {Object.keys(ayonEvent.summary).map((entityType) => (
                <tr key={entityType}>
                  <td>{entityType}</td>
                  {ayonEvent.summary[entityType].error ? (
                    <td>
                      <OverflowField value={ayonEvent.summary[entityType].error}></OverflowField>
                    </td>
                  ) : (
                    <td>{Math.round(ayonEvent.summary[entityType].progression * 100)}%</td>
                  )}
                </tr>
              ))}
            </tbody>
          </Table>
        </>
      }
      {ayonEvent != null && ayonEvent.status == null && (
        <ErrorContainer>
          Does Aquarium addon processor is running ?
        </ErrorContainer>
      )}
      {error && (
        <ErrorContainer>
          {error}
        </ErrorContainer>
      )}
    </Dialog>
  );
};

export default EventDialog