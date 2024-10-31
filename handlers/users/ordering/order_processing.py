from aiogram import types
from loader import dp, db, bot
from aiogram.dispatcher import FSMContext
from keyboards.inline import ordering
from states.ordering import OrderProcessingState


@dp.callback_query_handler()
async def start_processing(call: types.CallbackQuery, state: FSMContext):
    await OrderProcessingState.processing.set()

    order_id = int(call.data)
    await state.update_data(order_id=order_id)

    await db.change_processing(order_id)
    order = await db.select_order(order_id=order_id)

    if order[2]:
        # order has been processed
        if order[3]:
            await call.message.edit_text(
                '<i>Заказ обработан.</i> ✅',
                reply_markup=None
            )
            return

        # order is being processed
        await call.message.edit_text(
            "<i>Заказ обрабатывается другим менеджером.</i>",
            reply_markup=None
        )
    else:
        # precces the order
        await call.message.edit_text(
            order[1],
            reply_markup=ordering.processing_kb
        )


@dp.callback_query_handler(text='set_processed', state=OrderProcessingState.processing)
async def close_processing(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data.get('order_id')

    await db.set_processed(order_id)
    await call.message.edit_text(
        "<i>Заказ обработан!</i>",
        reply_markup=None
    )


@dp.callback_query_handler(text='quit_processing', state=OrderProcessingState.processing)
async def quit_processing(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    order_id = data.get('order_id')

    await db.change_processing(order_id)
    await call.message.edit_text(
        "<b>Вы отложили обработку заказа.</b>\nВернуться можете комадной /orders",  #TODO /orders command
        reply_markup=None
    )