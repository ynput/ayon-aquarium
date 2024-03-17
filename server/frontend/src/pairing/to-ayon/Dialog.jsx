import axios from "axios";
import addonData from "/src/common";

import { useEffect, useState } from "react";

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
  background-color: #0ca678;
  color: #ffffff;

  &:hover {
    background-color: #12b886;
  }
`;

const Hint = styled.i`
  color: #20c997;
`

const PairingToAyonDialog = ({ pairing, onHide }) => {
  const [ayonProjectName, setAyonProjectName] = useState();
  const [ayonProjectCode, setAyonProjectCode] = useState();
  const [showPairOnExisting, allowPairingOnExisting] = useState(false);
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

  const createProject = () => {
    setLoading(true);
    axios
      .post(
        `${addonData.baseUrl}/projects`,
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
        if (error.response.status === 409) {
          allowPairingOnExisting(true);
        }
        const errorMessage = error.response.data?.traceback ||
          error.response.data?.detail ||
          "Error on server, please check server's logs";
        setError(errorMessage);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  const pairProject = () => {
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
        <img height="100px" src="/ayon.png"></img>
        <h2>Create <strong>{pairing.aquariumProjectName}</strong> on Ayon</h2>
      </DialogTitle>
      <FormLayout>
        <FormRow label="Project name">
          <InputText
            value={ayonProjectName}
            onChange={(e) => {setAyonProjectName(e.target.value), allowPairingOnExisting(false)}}
          />
        </FormRow>
        <FormRow label="Project code">
          <InputText
            value={ayonProjectCode}
            disabled={showPairOnExisting == true}
            onChange={(e) => setAyonProjectCode(e.target.value)}
          />
        </FormRow>
        {showPairOnExisting !== true &&
          <FormRow>
            <PairButton label="Create on Ayon" icon="add" onClick={() => createProject()} />
          </FormRow>
        }
      </FormLayout>
      {error && (
        <ErrorContainer>
          {error}
          {showPairOnExisting &&
            <>
              <PairButton label="Pair to this existing project" icon="link" disabled={loading} onClick={() => pairProject()} />
              <Hint>Project anatomy won't be sync again</Hint>
            </>
          }
        </ErrorContainer>
      )}
      {loading && "Please wait..."}
    </Dialog>
  );
};

export default PairingToAyonDialog
