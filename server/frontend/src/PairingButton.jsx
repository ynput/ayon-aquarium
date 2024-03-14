import axios from "axios";
import addonData from "/src/common";

import { useEffect, useState, useRef } from "react";

import {
  Button,
  FormLayout,
  FormRow,
  InputText,
  OverflowField,
} from "@ynput/ayon-react-components";
import Dialog from "/src/components/Dialog";
import styled from "styled-components";

const DialogTitle = styled.h2`
  text-align: center;

  strong {
    color: #339af0;
    font-size: inherit;
    font-weight: inherit;
  }
`;

const ErrorContainer = styled.div`
  color: #ff6b6b;
  font-weight: bold;
  margin-top: 1rem;
  max-width: 400px;

`;

const ActionButton = styled(Button)`
  width: 140px;
`;

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

const PairingDialog = ({ pairing, onHide }) => {
  const [ayonProjectName, setAyonProjectName] = useState();
  const [ayonProjectCode, setAyonProjectCode] = useState();
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let name = pairing.aquariumProjectName;
    name = name.replace(/[^a-zA-Z0-9_]/g, "_");
    name = name.replace(/_+/g, "_");
    name = name.replace(/^_/, "");
    name = name.replace(/_$/, "");
    setAyonProjectName(name);

    let code = pairing.aquariumProjectCode || pairing.aquariumProjectName;
    code = code.replace(/[^a-zA-Z0-9]/g, "");
    code = code.replace(/_+/g, "");
    code = code.replace(/^_/, "");
    code = code.replace(/_$/, "");
    code = code.toLowerCase();
    code = code.substring(0, 6);
    setAyonProjectCode(code);
  }, [pairing]);

  const onPair = () => {
    setLoading(true);
    axios
      .post(
        `${addonData.baseUrl}/projects/pair`,
        {
          aquariumProjectKey: pairing.aquariumProjectKey,
          ayonProjectName: ayonProjectName,
          ayonProjectCode: ayonProjectCode,
        },
      )
      .then(() => {
        setError(null);
        onHide();
      })
      .catch((error) => {
        const errorMessage = error.response.data?.traceback ||
          error.response.data?.detail ||
          "Error on server, please check server's logs";
        setError(errorMessage);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  return (
    <Dialog visible={true} onHide={onHide}>
      <DialogTitle>
        Pair Aquarium's project <strong>{pairing.aquariumProjectName}</strong>
      </DialogTitle>
      <FormLayout>
        <FormRow label="Ayon project name">
          <InputText
            value={ayonProjectName}
            onChange={(e) => setAyonProjectName(e.target.value)}
          />
        </FormRow>
        <FormRow label="Ayon project code">
          <InputText
            value={ayonProjectCode}
            onChange={(e) => setAyonProjectCode(e.target.value)}
          />
        </FormRow>
        <FormRow>
          <Button label="Pair" onClick={onPair} />
        </FormRow>
      </FormLayout>
      {error && (
        <ErrorContainer>
          {error}
        </ErrorContainer>
      )}
      {loading && "Please wait..."}
    </Dialog>
  );
};

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
        <section>
          <DialogTitle>
            Syncing Aquarium's <strong>{ayonEvent.project_name} project</strong>
          </DialogTitle>
          <DialogTitle>
            <span>Sync <strong>{ayonEvent.status}</strong> for {totalEntities} entities.</span>
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
        </section>
      }
      {error && (
        <ErrorContainer>
          {error}
        </ErrorContainer>
      )}
    </Dialog>
  );
};

const PairingButton = ({ onPair, pairing }) => {
  const [showPairingDialog, setShowPairingDialog] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [syncStatus, setSyncStatus] = useState("Sync now");
  const [ayonEventId, setAyonEventId] = useState(null);

  // project is not paired yet show pairing button
  if (!pairing.ayonProjectName) {
    return (
      <>
        {showPairingDialog && (
          <PairingDialog
            pairing={pairing}
            onHide={() => {
              setShowPairingDialog(false);
              onPair();
            }}
          />
        )}
        <ActionButton
          label={`Pair project`}
          icon="link"
          onClick={() => {
            setShowPairingDialog(true);
          }}
        />
      </>
    );
  }

  const onSync = () => {
    setSyncStatus("Syncing...");
    setLoading(true);
    axios
      .post(`${addonData.baseUrl}/projects/${pairing.ayonProjectName}/sync`)
      .then(async (response) => {
        const eventId = response.data;
        setAyonEventId(eventId);
        setError(null);
        setSyncStatus("Sync triggered");
        onPair();
      })
      .catch((error) => {
        setSyncStatus("Sync error");
        const errorMessage = error.response.data?.traceback ||
          error.response.data?.detail ||
          "Error on server, please check server's logs";
        setError(errorMessage);
      })
      .finally(() => {
        setTimeout(() => {
          setSyncStatus("Sync now");
          setLoading(false);
          setError(null);
        }, 5000);
      });
  };

  return (
    <>
      {ayonEventId != null && (
        <EventDialog
          ayonEventId={ayonEventId}
          onHide={() => {
            setAyonEventId(null);
            onPair();
          }}
        />
      )}
      <ActionButton
        tooltip={error}
        label={syncStatus}
        icon={loading ? (error ? "error" : "done") : "sync"}
        disabled={syncStatus != "Sync now"}
        onClick={onSync}
      />
    </>
  );
};

export default PairingButton;
