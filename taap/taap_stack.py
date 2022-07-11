from aws_cdk import (
    # Duration,
    Stack,
    aws_dynamodb as ddb,
    aws_secretsmanager as sm,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_events as events,
    aws_events_targets as targets,
)
from constructs import Construct

class TaapStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here



        discord_secret = sm.Secret(self, 'DiscordAuthBot')
        infura_url_secret = sm.Secret(self, 'InfuraUrl')

        block_read_table = ddb.Table(
            self, 'BlockNumberTracker',
            partition_key={'name': 'app', 'type': ddb.AttributeType.STRING},
        )

        discord_users_table = ddb.Table(
            self, 'DiscordUsers',
            partition_key={'name': 'address', 'type': ddb.AttributeType.STRING},
        )

        user_access_table = ddb.Table(
            self, 'UserAccess',
            partition_key={'name': 'address', 'type': ddb.AttributeType.STRING},
            sort_key={"name": "token_id", 'type': ddb.AttributeType.NUMBER, }
        )

        web3_layer = _lambda.LayerVersion(self, 'lambda-layer',
                                            code=_lambda.AssetCode('lambda/layer/'),
                                            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
                                            )

        quarter_hour_rule = events.Rule(
            self, "QuarterHourRule",
            schedule=events.Schedule.cron(
                minute='*/15',
                hour='*',
                month='*',
                week_day='*',
                year='*'),
        )

        daily_rule = events.Rule(
            self, "Rule",
            schedule=events.Schedule.cron(
                minute='0',
                hour='8',
                month='*',
                week_day='*',
                year='*'),
        )

        event_read_lamda = _lambda.Function(
            self, 'EventReaderHandle',
            handler='event_read.handle',
            code=_lambda.Code.from_asset('lambda/app'),
            runtime=_lambda.Runtime.PYTHON_3_9,
            layers=[web3_layer],
            environment={
                'BLOCK_TABLE_NAME': block_read_table.table_name,
                'DISCORD_USERS_TABLE_NAME': discord_users_table.table_name,
                'USER_ACCESS_TABLE_NAME': user_access_table.table_name,
                'INFURA_URL_ARN': infura_url_secret.secret_full_arn,
                'DISCORD_AUTH_BOT_ARN': discord_secret.secret_full_arn,
            }
        )

        remove_expired_lambda = _lambda.Function(
            self, 'RemoveExpiredHandle',
            handler='remove_expired_roles.handle',
            code=_lambda.Code.from_asset('lambda/app'),
            runtime=_lambda.Runtime.PYTHON_3_9,
            layers=[web3_layer],
            environment={
                'DISCORD_USERS_TABLE_NAME': discord_users_table.table_name,
                'USER_ACCESS_TABLE_NAME': user_access_table.table_name,
                'DISCORD_AUTH_BOT_ARN': discord_secret.secret_full_arn,
            }
        )

        user_check_lambda = _lambda.Function(
            self, 'UserCheckHandler',
            handler='user_check.handle',
            code=_lambda.Code.from_asset('lambda/app'),
            runtime=_lambda.Runtime.PYTHON_3_9,
            environment={
                'TOOLS_USERS_TABLE_NAME': user_access_table.table_name,
            }
        )

        add_discord_user_lambda = _lambda.Function(
            self, 'AddDiscordHandler',
            handler='add_discord_user.handle',
            code=_lambda.Code.from_asset('lambda/app'),
            runtime=_lambda.Runtime.PYTHON_3_9,
            layers=[web3_layer],
            environment={
                'DISCORD_USERS_TABLE_NAME': discord_users_table.table_name,
            }
        )

        infura_url_secret.grant_read(event_read_lamda)
        discord_secret.grant_read(event_read_lamda)
        discord_secret.grant_read(remove_expired_lambda)

        quarter_hour_rule.add_target(targets.LambdaFunction(event_read_lamda))
        daily_rule.add_target(targets.LambdaFunction(remove_expired_lambda))

        discord_users_table.grant_read_write_data(add_discord_user_lambda)
        discord_users_table.grant_read_data(event_read_lamda)
        discord_users_table.grant_read_data(remove_expired_lambda)

        block_read_table.grant_read_write_data(event_read_lamda)

        user_access_table.grant_read_write_data(event_read_lamda)
        user_access_table.grant_read_data(user_check_lambda)
        user_access_table.grant_read_write_data(remove_expired_lambda)

        apigw.LambdaRestApi(self, 'AccessCheckEndPoint', handler=user_check_lambda)
        apigw.LambdaRestApi(self, 'AddDiscordUserEndPoint', handler=add_discord_user_lambda)
