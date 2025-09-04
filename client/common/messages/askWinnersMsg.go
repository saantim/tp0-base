package messages

type AskWinnersMsg struct {
	Agency uint8
}

func (m AskWinnersMsg) GetType() MsgType {
	return AskWinnersMsgType
}

func (m *AskWinnersMsg) ToBytes() []byte {
	buf := make([]byte, HeaderLen+AgencyLen)

	buf[0] = uint8(m.GetType())
	buf[HeaderLen] = m.Agency
	return buf
}
