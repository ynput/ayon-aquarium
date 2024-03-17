import {
  Button,
} from "@ynput/ayon-react-components";
import styled from "styled-components";

export const DialogTitle = styled.div`
  display: flex;
  align-items: center;
  flex-direction: column;
  width: 100%;
  gap: 8px;
  text-align: center;

  h2 {
    margin: 0;
  }

  strong {
    color: #339af0;
    font-size: inherit;
    font-weight: inherit;
  }
`;

export const ErrorContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
  color: #ff6b6b;
  font-weight: bold;
  margin-top: 1rem;
  width: 100%;
`;

export const AyonButton = styled(Button)`
  width: 100%;
  background-color: #0ca678;
  color: #ffffff;

  &:hover {
    background-color: #12b886;
  }
`

export const AquariumButton = styled(Button)`
  width: 100%;
  background-color: #1c7ed6;
  color: #ffffff;

  &:hover {
    background-color: #228be6;
  }
`