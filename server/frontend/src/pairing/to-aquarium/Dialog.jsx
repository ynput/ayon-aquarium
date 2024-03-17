import axios from "axios";
import addonData from "/src/common";

import { useState, useEffect } from "react";

import {
  Button,
  FormLayout,
  FormRow,
  InputText,
} from "@ynput/ayon-react-components";
import Dialog from "/src/components/Dialog";
import styled from "styled-components";
import { ErrorContainer, DialogTitle } from '/src/components/Styles'

const PairButton = styled(Button)`
  width: 100%;
  background-color: #1c7ed6;
  color: #ffffff;

  &:hover {
    background-color: #228be6;
  }
`;


const PairingToAquariumDialog = ({ pairing, onHide }) => {
  const [aquariumProjectName, setAquariumProjectName] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setAquariumProjectName(pairing.ayonProjectName);
  }, [pairing]);

  const createProject = () => {
    setLoading(true);
    axios
      .post(
        `${addonData.baseUrl}/projects`,
        {
          aquariumProjectName: aquariumProjectName,
          aquariumProjectKey: pairing.aquariumProjectKey,
          ayonProjectName: pairing.ayonProjectName,
          ayonProjectCode: pairing.ayonProjectCode,
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
        <img height="100px" src="/aquarium.png"></img>
        <h2>Create <strong>{pairing.ayonProjectName}</strong> on Aquarium</h2>
      </DialogTitle>
      <FormLayout>
        <FormRow label="Project name">
          <InputText
            value={aquariumProjectName}
            onChange={(e) => {setAquariumProjectName(e.target.value)}}
          />
        </FormRow>
        <FormRow>
          <PairButton label="Create on Aquarium" icon="add" disabled={loading} onClick={() => createProject()} />
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

export default PairingToAquariumDialog
