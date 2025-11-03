from algopy import (
    ARC4Contract,
    String,
    UInt64,
    arc4,
    Global,
    Txn,
    itxn,
    subroutine,
    urange,
)
from algopy.arc4 import abimethod


class AlgoCdtStable(ARC4Contract):
    # State variables
    asset_id: UInt64
    name: String
    symbol: String
    decimals: UInt64
    total_supply: UInt64
    cap: UInt64
    reserve_addr: arc4.Address
    allowances: arc4.DynamicArray[arc4.Tuple[arc4.Address, arc4.DynamicArray[arc4.Tuple[arc4.Address, UInt64]]]]
    minters: arc4.DynamicArray[arc4.Address]

    def __init__(self) -> None:
        self.allowances = arc4.DynamicArray[arc4.Tuple[arc4.Address, arc4.DynamicArray[arc4.Tuple[arc4.Address, UInt64]]]]()
        self.minters = arc4.DynamicArray[arc4.Address]()
        # Add deployer as initial minter
        self.minters.append(arc4.Address(Txn.sender))

    @abimethod()
    def create_asa(
        self,
        name_: String,
        symbol_: String,
        decimals_: UInt64,
        cap_: UInt64,
        reserve_addr: arc4.Address,
    ) -> UInt64:
        # Only deployer can create ASA
        assert arc4.Address(Txn.sender) == arc4.Address(Global.creator_address), "Only deployer can create ASA"

        self.name = name_
        self.symbol = symbol_
        self.decimals = decimals_
        self.cap = cap_
        self.reserve_addr = reserve_addr
        self.total_supply = UInt64(0)

        # Create ASA with total = cap, clawback = app, reserve = reserve_addr
        result = itxn.AssetConfig(
            total=cap_,
            decimals=decimals_,
            default_frozen=False,
            unit_name=symbol_,
            asset_name=name_,
            manager=Global.current_application_address,
            reserve=reserve_addr.native,
            freeze=Global.current_application_address,
            clawback=Global.current_application_address,
            url="https://casadotoken.com.br/",
            fee=Global.min_txn_fee,
        ).submit()

        # ID do ASA criado pela inner tx
        self.asset_id = result.created_asset.id

        return self.asset_id

    @abimethod()
    def set_asset(self, asset_id_: UInt64, reserve_addr_: arc4.Address) -> None:
        # Only deployer can set asset
        assert arc4.Address(Txn.sender) == arc4.Address(Global.creator_address), "Only deployer can set asset"

        self.asset_id = asset_id_
        self.reserve_addr = reserve_addr_

        # Reconfigure ASA (ex.: garantir clawback = app)
        itxn.AssetConfig(
            config_asset=asset_id_,
            clawback=Global.current_application_address,
            fee=Global.min_txn_fee,
        ).submit()

    @abimethod()
    def mint(self, to: arc4.Address, amount: UInt64) -> None:
        assert self._is_minter(arc4.Address(Txn.sender)), "Caller is not a minter"
        self._mint(to, amount)

    @subroutine
    def _mint(self, to: arc4.Address, amount: UInt64) -> None:
        assert self.total_supply + amount <= self.cap, "Cap exceeded"
        self.total_supply += amount

        # Mint via clawback transfer from the app escrow to the recipient
        itxn.AssetTransfer(
            xfer_asset=self.asset_id,
            asset_amount=amount,
            asset_sender=Global.current_application_address,
            asset_receiver=to.native,
            fee=Global.min_txn_fee,  # importante
        ).submit()

    @abimethod()
    def burn(self, amount: UInt64) -> None:
        self._burn(arc4.Address(Txn.sender), amount)

    @abimethod()
    def burn_from(self, account: arc4.Address, amount: UInt64) -> None:
        allowance = self._get_allowance(account, arc4.Address(Txn.sender))
        assert allowance >= amount, "Burn amount exceeds allowance"
        self._approve(account, arc4.Address(Txn.sender), allowance - amount)
        self._burn(account, amount)

    @subroutine
    def _burn(self, account: arc4.Address, amount: UInt64) -> None:
        self.total_supply -= amount

        # Burn via clawback transfer from account back into the app escrow
        itxn.AssetTransfer(
            xfer_asset=self.asset_id,
            asset_amount=amount,
            asset_sender=account.native,
            asset_receiver=Global.current_application_address,
            fee=Global.min_txn_fee,  # importante
        ).submit()

    @abimethod()
    def transfer(self, to: arc4.Address, amount: UInt64) -> None:
        self._transfer(arc4.Address(Txn.sender), to, amount)

    @abimethod()
    def transfer_from(self, from_: arc4.Address, to: arc4.Address, amount: UInt64) -> None:
        allowance = self._get_allowance(from_, arc4.Address(Txn.sender))
        assert allowance >= amount, "Transfer amount exceeds allowance"
        self._approve(from_, arc4.Address(Txn.sender), allowance - amount)
        self._transfer(from_, to, amount)

    @subroutine
    def _transfer(self, from_: arc4.Address, to: arc4.Address, amount: UInt64) -> None:
        # Transferência via clawback (o app é o clawback configurado no ASA)
        itxn.AssetTransfer(
            xfer_asset=self.asset_id,
            asset_amount=amount,
            asset_sender=from_.native,
            asset_receiver=to.native,
            fee=Global.min_txn_fee,  # importante
        ).submit()

    @abimethod()
    def approve(self, spender: arc4.Address, amount: UInt64) -> None:
        self._approve(arc4.Address(Txn.sender), spender, amount)

    @subroutine
    def _approve(self, owner: arc4.Address, spender: arc4.Address, amount: UInt64) -> None:
        # Update allowances in state
        owner_allowances = self._get_owner_allowances(owner)
        spender_found = False
        for i in urange(owner_allowances.length):
            if owner_allowances[i][0] == spender:
                owner_allowances[i] = arc4.Tuple((spender, amount))
                spender_found = True
                break
        if not spender_found:
            owner_allowances.append(arc4.Tuple((spender, amount)))

        # Update the allowances array
        for i in urange(self.allowances.length):
            if self.allowances[i][0] == owner:
                self.allowances[i] = arc4.Tuple((owner, owner_allowances.copy()))
                return
        self.allowances.append(arc4.Tuple((owner, owner_allowances)))

    @abimethod()
    def allowance(self, owner: arc4.Address, spender: arc4.Address) -> UInt64:
        return self._get_allowance(owner, spender)

    @subroutine
    def _get_allowance(self, owner: arc4.Address, spender: arc4.Address) -> UInt64:
        owner_allowances = self._get_owner_allowances(owner)
        for allowance in owner_allowances:
            if allowance[0] == spender:
                return allowance[1]
        return UInt64(0)

    @subroutine
    def _get_owner_allowances(self, owner: arc4.Address) -> arc4.DynamicArray[arc4.Tuple[arc4.Address, UInt64]]:
        for i in urange(self.allowances.length):
            if self.allowances[i][0] == owner:
                return self.allowances[i][1]
        return arc4.DynamicArray[arc4.Tuple[arc4.Address, UInt64]]()

    @abimethod()
    def balance_of(self, account: arc4.Address) -> UInt64:
        # Placeholder: consultar via indexer/SDK off-chain ou implementar leitura com assets/Accounts.
        return UInt64(0)

    @abimethod()
    def add_minter(self, account: arc4.Address) -> None:
        assert self._is_minter(arc4.Address(Txn.sender)), "Caller is not a minter"
        if not self._is_minter(account):
            self.minters.append(account)

    @abimethod()
    def remove_minter(self, account: arc4.Address) -> None:
        assert self._is_minter(arc4.Address(Txn.sender)), "Caller is not a minter"
        assert account != arc4.Address(Txn.sender), "Cannot remove self"
        new_minters = arc4.DynamicArray[arc4.Address]()
        for minter in self.minters:
            if minter != account:
                new_minters.append(minter)
        self.minters = new_minters.copy()

    @abimethod()
    def is_minter(self, account: arc4.Address) -> bool:
        return self._is_minter(account)

    @subroutine
    def _is_minter(self, account: arc4.Address) -> bool:
        for minter in self.minters:
            if minter == account:
                return True
        return False

    @abimethod()
    def get_total_supply(self) -> UInt64:
        return self.total_supply

    @abimethod()
    def get_cap(self) -> UInt64:
        return self.cap

    @abimethod()
    def set_reserve(self, reserve_addr_: arc4.Address) -> None:
        # Only deployer can set reserve
        assert arc4.Address(Txn.sender) == arc4.Address(Global.creator_address), "Only deployer can set reserve"
        self.reserve_addr = reserve_addr_
