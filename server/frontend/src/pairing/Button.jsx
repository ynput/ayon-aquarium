import { useState } from "react";

import { AyonButton, AquariumButton, ButtonGroup } from "../components/Styles";

import toAyonDialog from "./to-ayon/Dialog";
import ToAyonSyncButton from './to-ayon/Sync';
import toAquariumDialog from "./to-aquarium/Dialog";

const PairingButton = ({ refresh, pairing }) => {
  const [showPairingDialog, setShowPairingDialog] = useState(false);

  const PairingDialog = pairing.ayonProjectName ? toAquariumDialog : toAyonDialog;
  const PairingButton = pairing.ayonProjectName ? AquariumButton : AyonButton;

  // project is not paired yet show pairing button
  if (!pairing.ayonProjectName || !pairing.aquariumProjectKey) {
    return (
      <>
        {showPairingDialog && (
          <PairingDialog
            pairing={pairing}
            onHide={() => {
              setShowPairingDialog(false);
              refresh();
            }}
          />
        )}
        <ButtonGroup>
          <PairingButton
            tooltip="Create and sync project's entities"
            label={pairing.aquariumProjectKey ? 'Create on Ayon' : 'Create on Aquarium'}
            icon="add"
            onClick={() => {
              setShowPairingDialog(true);
            }}
          />
        </ButtonGroup>
      </>
    );
  }

  return <ToAyonSyncButton refresh={refresh} pairing={pairing} />
};

export default PairingButton;
