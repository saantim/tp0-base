package messages

type AskWinnersMsg struct {
	Agency uint8
}

// GetType returns the message type identifier for AskWinnersMsg.
func (m AskWinnersMsg) GetType() MsgType {
	return AskWinnersMsgType
}

// ToBytes serializes the AskWinnersMsg into a byte slice.
func (m *AskWinnersMsg) ToBytes() []byte {
	buf := make([]byte, HeaderLen+AgencyLen)

	buf[0] = uint8(m.GetType())
	buf[HeaderLen] = m.Agency
	return buf
}
