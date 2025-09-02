package messages

import "github.com/7574-sistemas-distribuidos/docker-compose-init/client/common/model"

type BetMsg struct {
	Bet model.Bet
}

const BetMsgPayloadLen = model.TotalFixedLen

func (b *BetMsg) GetType() MsgType {
	return BetMsgType
}

func (b *BetMsg) ToBytes() []byte {
	betBytes := b.Bet.ToBytes()
	buf := make([]byte, HeaderLen+BetMsgPayloadLen)

	buf[0] = uint8(b.GetType())
	copy(buf[HeaderLen:], betBytes)

	return buf
}
