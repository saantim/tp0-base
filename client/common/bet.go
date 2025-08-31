package common

import "encoding/binary"

type Bet struct {
	ID       uint32
	Name     string
	LastName string
	BirthDay string
	BetNum   uint32
}

const (
	idLen         = 4
	nameLen       = 32
	lastNameLen   = 32
	birthDayLen   = 10
	betNumLen     = 4
	totalFixedLen = idLen + nameLen + lastNameLen + birthDayLen + betNumLen
)

func (b *Bet) ToBytes() []byte {
	buf := make([]byte, totalFixedLen)
	i := 0

	binary.BigEndian.PutUint32(buf[i:i+idLen], b.ID)
	i += idLen

	copy(buf[i:i+nameLen], b.Name)
	i += nameLen

	copy(buf[i:i+lastNameLen], b.LastName)
	i += lastNameLen

	copy(buf[i:i+birthDayLen], b.BirthDay)
	i += birthDayLen

	binary.BigEndian.PutUint32(buf[i:i+betNumLen], b.BetNum)

	return buf
}
