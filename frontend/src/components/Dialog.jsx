import styled from 'styled-components'
import { Panel, Icon } from '@ynput/ayon-react-components'

const Shade = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  `

const DialogWindow = styled(Panel)`
  min-width: 30vw;
  max-width: 40vw;
  min-height: 300px;
  padding: 32px;
  border-radius: 8px;
  gap: 16px;
  border: 2px solid var(--md-sys-color-inverse-on-surface);
  box-shadow: 0 0 44px 20px #000, rgb(50 72 93 / 65%) 0px 50px 100px -20px,rgba(0, 0, 0, 1) 0px 30px 60px -30px;
  position: relative;
`

const Close = styled(Icon)`
    position: absolute;
    top: 16px;
    right: 16px;
    cursor: pointer;

    &:hover {
        opacity: 0.8;
    }
`


const Dialog = ({ visible, onHide, children }) => {

  if (!visible) {
    return null
  }

  const handleClose = (event) => {
    if (event.currentTarget !== event.target) return
    event.preventDefault()
    onHide()
  }

  return (
    <Shade onClick={handleClose}>
      <DialogWindow>
        <Close icon="close" onClick={handleClose}></Close>
        {children}
      </DialogWindow>
    </Shade>
  )
}

export default Dialog
