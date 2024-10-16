import axios from "axios";
import addonData from "/src/common";

import EventDialog from "./EventDialog";

import { useState } from "react";
import { Button } from "@ynput/ayon-react-components";
import styled from "styled-components";
import { ButtonGroup } from "/src/components/Styles";

const ActionButton = styled(Button)`
  width: 100%;
`;

const UnpairButton = styled(Button)`
  width: 40px;
  background-color: #ff6b6b;
  color: #ffe3e3;

  &:hover {
    background-color: #ff8787;
  }
`;

const SyncButton = ({ refresh, pairing }) => {
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [syncStatus, setSyncStatus] = useState("Sync to Ayon");
  const [ayonEventId, setAyonEventId] = useState(null);
  const [unpairing, setUnpairing] = useState(false);

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
        refresh();
      })
      .catch((error) => {
        setSyncStatus("Sync error");
        const errorMessage = error.response?.data?.traceback ||
          error.response?.data?.detail ||
          "Error on server, please check server's logs";
        setError(errorMessage);
      })
      .finally(() => {
        setTimeout(() => {
          setSyncStatus("Sync to Ayon");
          setLoading(false);
          setError(null);
        }, 5000);
      });
  };

  const unpair = () => {
    setUnpairing(true)
    axios
      .delete(`${addonData.baseUrl}/projects/${pairing.ayonProjectName}/pair`)
      .then(refresh).finally(() => {
        setUnpairing(false)
      })
  };

      return (
    <>
      {ayonEventId != null && (
        <EventDialog
          ayonEventId={ayonEventId}
          onHide={() => {
            setAyonEventId(null);
            refresh();
          }}
        />
      )}
      <ButtonGroup>
        <ActionButton
          tooltip={error ? error : "Sync all your project's entities"}
          label={syncStatus}
          icon={loading ? (error ? "error" : "done") : "sync"}
          disabled={syncStatus != "Sync to Ayon"}
          onClick={onSync}
        />
        <UnpairButton
          tooltip="Unpair project"
          icon="link_off"
          disabled={unpairing}
          onClick={unpair}
        />
      </ButtonGroup>
    </>
  );

}

export default SyncButton