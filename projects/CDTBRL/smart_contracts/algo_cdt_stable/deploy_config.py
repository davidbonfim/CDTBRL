import logging

import algokit_utils

logger = logging.getLogger(__name__)
             

# define deployment behaviour based on supplied app spec
def deploy() -> None:
    from smart_contracts.artifacts.algo_cdt_stable.algo_cdt_stable_client import (
        CreateAsaArgs,
        AlgoCdtStableFactory,
    )

    algorand = algokit_utils.AlgorandClient.from_environment()
    deployer_ = algorand.account.from_environment("DEPLOYER")

    factory = algorand.client.get_typed_app_factory(
        AlgoCdtStableFactory, default_sender=deployer_.address
    )

    app_client, result = factory.deploy(
        on_update=algokit_utils.OnUpdate.AppendApp,
        on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
    )

    if result.operation_performed in [
        algokit_utils.OperationPerformed.Create,
        algokit_utils.OperationPerformed.Replace,
    ]:
        algorand.send.payment(
            algokit_utils.PaymentParams(
                amount=algokit_utils.AlgoAmount(algo=1),
                sender=deployer_.address,
                receiver=app_client.app_address,
            )
        )

    # Create ASA with initial parameters
    name = "CDTBRL"
    symbol = "CDTBRL"
    decimals = 6  # For stablecoin precision
    cap = 100_000_000_000 * (10 ** decimals)  # 100 billion tokens max
    reserve_addr = deployer_.address  # Use deployer as initial reserve

    response = app_client.send.create_asa(
        args=CreateAsaArgs(
            name_=name,
            symbol_=symbol,
            decimals_=decimals,
            cap_=cap,
            reserve_addr=reserve_addr,
        )
    )
    asset_id = response.abi_return
    logger.info(
        f"Created ASA {asset_id} for {app_client.app_name} ({app_client.app_id}) "
        f"with name={name}, symbol={symbol}, decimals={decimals}, cap={cap}, reserve_addr={reserve_addr}"
    )
